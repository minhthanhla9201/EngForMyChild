"""
Test khu catalog: model, view (login + nội dung), lệnh import CSV, audio (mock TTS).

TTS/IPA được MOCK — không gọi mạng/đọc loa thật, chỉ kiểm logic cache/idempotent.
"""

import io
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import ManagePasscode

from . import imports as import_service
from .models import AudioClip, Topic, Word


class CatalogViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('parent', password='pass12345')
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        cls.word = Word.objects.create(topic=cls.topic, text_en='cat', text_vi='con mèo')

    def test_topic_list_requires_login(self):
        """Chưa đăng nhập → redirect login."""
        resp = self.client.get(reverse('catalog:topic_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), resp.url)

    def test_topic_and_word_list(self):
        """Đăng nhập → thấy chủ đề và từ trong chủ đề."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('catalog:topic_list'))
        self.assertContains(resp, 'Động vật')
        resp2 = self.client.get(reverse('catalog:word_list', args=['animals']))
        self.assertContains(resp2, 'cat')
        self.assertContains(resp2, 'con mèo')

    @mock.patch('catalog.audio.tts.synthesize_to_file', return_value='pyttsx3')
    def test_word_audio_generates_and_caches(self, mock_tts):
        """API audio: lần đầu sinh (gọi TTS), lần sau dùng cache (không gọi lại)."""
        self.client.login(username='parent', password='pass12345')
        url = reverse('catalog:word_audio', args=[self.word.pk])

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['ok'])
        self.assertEqual(AudioClip.objects.filter(word=self.word).count(), 1)
        self.assertEqual(mock_tts.call_count, 1)

        # Lần 2: đã có clip → KHÔNG gọi TTS thêm.
        self.client.get(url)
        self.assertEqual(mock_tts.call_count, 1)
        self.assertEqual(AudioClip.objects.filter(word=self.word).count(), 1)

    @mock.patch('catalog.audio.tts.synthesize_to_file', return_value=None)
    def test_word_audio_failure_returns_503(self, _mock):
        """TTS lỗi (offline) → trả 503 thân thiện, không 500."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('catalog:word_audio', args=[self.word.pk]))
        self.assertEqual(resp.status_code, 503)
        self.assertFalse(resp.json()['ok'])


class ImportWordsCommandTests(TestCase):
    """Test lệnh import_words: tạo đúng + idempotent + sinh IPA (mock)."""

    CSV = 'topic,text_en,text_vi\nAnimals,dog,con chó\nColors,red,màu đỏ\n'

    def _run_import(self):
        # Ghi CSV tạm rồi gọi lệnh với --no-audio (test không sinh audio thật).
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(self.CSV)
            path = f.name
        out = io.StringIO()
        with mock.patch('catalog.ipa.to_ipa', return_value='ɪpa'):
            call_command('import_words', path, '--no-audio', stdout=out)
        return out.getvalue()

    def test_import_creates_topics_and_words(self):
        self._run_import()
        self.assertEqual(Topic.objects.count(), 2)
        self.assertEqual(Word.objects.count(), 2)
        dog = Word.objects.get(text_en='dog')
        self.assertEqual(dog.text_vi, 'con chó')
        self.assertEqual(dog.phonetic, 'ɪpa')  # IPA tự sinh (mock)

    def test_import_is_idempotent(self):
        """Chạy 2 lần → không tạo trùng từ/chủ đề."""
        self._run_import()
        self._run_import()
        self.assertEqual(Topic.objects.count(), 2)
        self.assertEqual(Word.objects.count(), 2)


class CatalogManageViewTests(TestCase):
    """
    Test khu quản lý (phụ huynh): CRUD chủ đề/từ + nhập CSV qua web.

    Khu quản lý cần đăng nhập + mở khoá passcode (xem core.decorators.manage_required).
    """

    PASSCODE = '4321'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('parent', password='pass12345')
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        cls.word = Word.objects.create(topic=cls.topic, text_en='cat', text_vi='con mèo')

    def _unlock(self):
        """Đăng nhập + đặt passcode + mở khoá khu quản lý."""
        self.client.login(username='parent', password='pass12345')
        ManagePasscode.get_solo().set_passcode(self.PASSCODE)
        self.client.post(reverse('accounts:manage_unlock'), {'passcode': self.PASSCODE})

    # --- Yêu cầu mở khoá (đăng nhập + passcode) ---
    def test_manage_views_require_unlock(self):
        """Chưa mở khoá → mọi màn quản lý chuyển về màn nhập passcode."""
        self.client.login(username='parent', password='pass12345')
        ManagePasscode.get_solo().set_passcode(self.PASSCODE)
        for name in ('topic_manage', 'topic_add', 'word_manage', 'word_add', 'word_import', 'word_export'):
            resp = self.client.get(reverse(f'catalog_manage:{name}'))
            self.assertEqual(resp.status_code, 302, name)
            self.assertIn(reverse('accounts:manage_unlock'), resp.url, name)

    # --- Chủ đề ---
    def test_topic_list_shows_word_count(self):
        self._unlock()
        resp = self.client.get(reverse('catalog_manage:topic_manage'))
        self.assertContains(resp, 'Động vật')
        self.assertEqual(resp.context['topics'][0].num_words, 1)

    def test_topic_add_autoslug(self):
        """Tạo chủ đề bỏ trống slug → tự sinh từ name_en."""
        self._unlock()
        resp = self.client.post(reverse('catalog_manage:topic_add'),
                                {'name_en': 'Colors', 'name_vi': 'Màu sắc',
                                 'slug': '', 'icon': '🎨', 'order': 0, 'active': 'Y'})
        self.assertRedirects(resp, reverse('catalog_manage:topic_manage'))
        self.assertTrue(Topic.objects.filter(slug='colors').exists())

    def test_topic_edit(self):
        self._unlock()
        resp = self.client.post(reverse('catalog_manage:topic_edit', args=[self.topic.pk]),
                                {'name_en': 'Animals', 'name_vi': 'Thú vật',
                                 'slug': 'animals', 'icon': '🐶', 'order': 1, 'active': 'Y'})
        self.assertRedirects(resp, reverse('catalog_manage:topic_manage'))
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.name_vi, 'Thú vật')

    # --- Từ vựng ---
    def test_word_manage_filter_and_search(self):
        self._unlock()
        Word.objects.create(topic=self.topic, text_en='dog', text_vi='con chó')
        # Lọc theo chủ đề: thấy cả 2 từ.
        resp = self.client.get(reverse('catalog_manage:word_manage'), {'topic': 'animals'})
        self.assertContains(resp, 'cat')
        self.assertContains(resp, 'dog')
        # Tìm theo từ: chỉ thấy 'cat'.
        resp2 = self.client.get(reverse('catalog_manage:word_manage'), {'q': 'cat'})
        self.assertContains(resp2, 'cat')
        self.assertNotContains(resp2, '>dog<')

    @mock.patch('catalog.views.ipa_service.to_ipa', return_value='dɒg')
    def test_word_add_autogenerates_ipa(self, _mock):
        """Thêm từ bỏ trống IPA → tự sinh (mock eng-to-ipa)."""
        self._unlock()
        resp = self.client.post(reverse('catalog_manage:word_add'),
                                {'topic': self.topic.pk, 'text_en': 'dog', 'text_vi': 'con chó',
                                 'phonetic': '', 'level': 1, 'active': 'Y'})
        self.assertRedirects(resp, reverse('catalog_manage:word_manage'))
        dog = Word.objects.get(text_en='dog')
        self.assertEqual(dog.phonetic, 'dɒg')

    def test_word_edit(self):
        self._unlock()
        resp = self.client.post(reverse('catalog_manage:word_edit', args=[self.word.pk]),
                                {'topic': self.topic.pk, 'text_en': 'cat', 'text_vi': 'mèo con',
                                 'phonetic': 'kæt', 'level': 1, 'active': 'Y'})
        self.assertRedirects(resp, reverse('catalog_manage:word_manage'))
        self.word.refresh_from_db()
        self.assertEqual(self.word.text_vi, 'mèo con')

    # --- Nhập CSV qua web ---
    def test_word_import_via_web(self):
        """Upload CSV qua web → tạo đúng chủ đề/từ (no-audio: make_audio off)."""
        self._unlock()
        csv_bytes = b'topic,text_en,text_vi\nColors,red,mau do\n'
        upload = SimpleUploadedFile('words.csv', csv_bytes, content_type='text/csv')
        with mock.patch('catalog.imports.ipa_service.to_ipa', return_value=''):
            resp = self.client.post(reverse('catalog_manage:word_import'),
                                    {'csv_file': upload})  # make_audio off (không tick)
        self.assertRedirects(resp, reverse('catalog_manage:word_manage'))
        self.assertTrue(Word.objects.filter(text_en='red').exists())

    def test_word_import_rejects_non_csv(self):
        """File không phải .csv → form lỗi, không nhập."""
        self._unlock()
        upload = SimpleUploadedFile('words.txt', b'x', content_type='text/plain')
        resp = self.client.post(reverse('catalog_manage:word_import'), {'csv_file': upload})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '.csv')

    # --- Xuất CSV (backup) ---
    def test_word_export_downloads_csv_with_data(self):
        """Xuất CSV: trả file đính kèm, có tiêu đề đúng cột + dữ liệu từ."""
        self._unlock()
        resp = self.client.get(reverse('catalog_manage:word_export'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('attachment', resp['Content-Disposition'])
        self.assertIn('words_backup.csv', resp['Content-Disposition'])
        body = resp.content.decode('utf-8-sig')  # bỏ BOM
        self.assertIn('topic,topic_vi,text_en,text_vi,phonetic,level,image', body)
        self.assertIn('cat', body)
        self.assertIn('con mèo', body)

    def test_export_includes_image_path(self):
        """Từ có hình → cột image trong CSV chứa đường dẫn file (images/...)."""
        self._unlock()
        self.word.image = 'images/cat.jpg'
        self.word.save(update_fields=['image'])
        csv_text = import_service.export_words()
        self.assertIn('images/cat.jpg', csv_text)

    def test_export_then_import_roundtrip(self):
        """Round-trip: xuất ra CSV rồi nhập lại KHÔNG tạo trùng (khôi phục đúng)."""
        self._unlock()
        Word.objects.create(topic=self.topic, text_en='dog', text_vi='con chó')
        before_topics, before_words = Topic.objects.count(), Word.objects.count()

        csv_text = import_service.export_words()
        upload = SimpleUploadedFile('backup.csv', csv_text.encode('utf-8'),
                                    content_type='text/csv')
        resp = self.client.post(reverse('catalog_manage:word_import'), {'csv_file': upload})
        self.assertRedirects(resp, reverse('catalog_manage:word_manage'))
        # Nạp lại chính dữ liệu vừa xuất → số chủ đề/từ không đổi (idempotent).
        self.assertEqual(Topic.objects.count(), before_topics)
        self.assertEqual(Word.objects.count(), before_words)

    def test_import_sets_image_path(self):
        """CSV có cột image → gán đường dẫn hình cho từ (tạo mới và cập nhật)."""
        self._unlock()
        # Tạo mới kèm hình.
        csv_bytes = ('topic,text_en,text_vi,image\n'
                     'Animals,dog,con chó,images/dog.png\n').encode('utf-8')
        upload = SimpleUploadedFile('w.csv', csv_bytes, content_type='text/csv')
        with mock.patch('catalog.imports.ipa_service.to_ipa', return_value=''):
            self.client.post(reverse('catalog_manage:word_import'), {'csv_file': upload})
        dog = Word.objects.get(text_en='dog')
        self.assertEqual(dog.image.name, 'images/dog.png')

        # Nhập lại với hình khác → cập nhật (idempotent, không tạo trùng).
        csv2 = ('topic,text_en,text_vi,image\n'
                'Animals,dog,con chó,images/dog2.png\n').encode('utf-8')
        upload2 = SimpleUploadedFile('w2.csv', csv2, content_type='text/csv')
        with mock.patch('catalog.imports.ipa_service.to_ipa', return_value=''):
            self.client.post(reverse('catalog_manage:word_import'), {'csv_file': upload2})
        dog.refresh_from_db()
        self.assertEqual(dog.image.name, 'images/dog2.png')
        self.assertEqual(Word.objects.filter(text_en='dog').count(), 1)


class PraiseTests(TestCase):
    """Giọng động viên (edge-tts mock): sinh + cache + manifest + API."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('parent', password='pass12345')

    def setUp(self):
        # Cache giọng vào thư mục tạm để không đụng media thật của dự án.
        self._tmp = tempfile.mkdtemp()
        self._override = self.settings(MEDIA_ROOT=self._tmp)
        self._override.enable()

    def tearDown(self):
        self._override.disable()

    def _fake_edge(self, text, out_path, voice):
        """Giả lập edge-tts: ghi file mp3 rỗng (không gọi mạng)."""
        from pathlib import Path
        Path(out_path).write_bytes(b'ID3')

    def test_generate_all_creates_and_is_idempotent(self):
        """Sinh mp3 cho mọi câu động viên + lời khen huy hiệu; chạy lại thì bỏ qua."""
        from django.conf import settings
        from catalog import praise
        # generate_all giờ sinh PRAISE_LINES × 2 giọng (nữ + nam) + _hint_lines (nữ)
        # + _badge_lines (nam). Không còn _page_hint_lines vì PRAISE_LINES đã gồm chúng.
        voice = praise._default_voice()
        badge_voice = getattr(settings, 'TTS_VOICE_BADGE', 'vi-VN-NamMinhNeural')

        unique_files = set()
        # PRAISE_LINES: mỗi câu × 2 giọng
        for t in [ln for lines in praise.PRAISE_LINES.values() for ln in lines]:
            unique_files.add(praise.filename_for(t, voice))
            unique_files.add(praise.filename_for(t, badge_voice))
        # _hint_lines: giọng nữ
        for t in praise._hint_lines():
            unique_files.add(praise.filename_for(t, voice))
        # _badge_lines: giọng nam
        for t in praise._badge_lines():
            unique_files.add(praise.filename_for(t, badge_voice))
        with mock.patch('catalog.praise.tts._edge_tts_save', side_effect=self._fake_edge):
            gen, skip, fail = praise.generate_all()
            # Lần 1: mỗi FILE duy nhất được sinh đúng 1 lần (câu trùng → skip trong cùng lượt).
            self.assertEqual(gen, len(unique_files))
            self.assertEqual(fail, 0)
            # Idempotent — lần 2 KHÔNG sinh mới, không lỗi; mọi lượt lặp đều 'skip'.
            gen2, skip2, fail2 = praise.generate_all()
            self.assertEqual(gen2, 0)
            self.assertEqual(fail2, 0)
            self.assertEqual(skip2, gen + skip)  # tổng lượt lặp lần 1 = số skip lần 2

    def test_badge_voice_uses_different_voice(self):
        """Lời khen huy hiệu sinh bằng GIỌNG NAM (khác giọng động viên) → file khác."""
        from django.conf import settings
        from catalog import praise
        desc = praise._badge_lines()[0]
        # Cùng câu, 2 giọng → 2 tên file khác nhau (hash gồm cả giọng).
        f_female = praise.filename_for(desc, settings.TTS_VOICE_VI)
        f_male = praise.filename_for(desc, settings.TTS_VOICE_BADGE)
        self.assertNotEqual(f_female, f_male)
        with mock.patch('catalog.praise.tts._edge_tts_save', side_effect=self._fake_edge):
            praise.generate_all()
        # badge_voice_url trả URL giọng nam đã sinh.
        self.assertTrue(praise.badge_voice_url(desc).endswith('.mp3'))

    def test_generate_no_pyttsx3_fallback_on_failure(self):
        """edge-tts thất bại hẳn → tính là lỗi, KHÔNG tạo file (tránh giọng OS)."""
        from catalog import praise
        with mock.patch('catalog.praise.tts._edge_tts_save', side_effect=Exception('net')):
            gen, skip, fail = praise.generate_all()
            self.assertEqual(gen, 0)
            self.assertTrue(fail > 0)

    def test_manifest_lists_only_existing(self):
        """Manifest chỉ chứa URL của file đã sinh; chưa sinh → danh sách rỗng."""
        from catalog import praise
        empty = praise.manifest()
        self.assertEqual(empty['correct'], [])
        with mock.patch('catalog.praise.tts._edge_tts_save', side_effect=self._fake_edge):
            praise.generate_all()
        full = praise.manifest()
        self.assertTrue(len(full['correct']) > 0)
        self.assertTrue(all(u.endswith('.mp3') for u in full['correct']))

    def test_manifest_api_requires_login_and_returns_json(self):
        """API manifest: cần đăng nhập; trả JSON đúng cấu trúc."""
        url = reverse('catalog:praise_manifest')
        self.assertEqual(self.client.get(url).status_code, 302)  # chưa login → redirect
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['ok'])
        self.assertIn('correct', data['lines'])


# GIF 1x1 hợp lệ để test upload ImageField (Pillow đọc được).
GIF_1PX = (b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!'
           b'\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;')


class TopicIconTests(TestCase):
    """Icon chủ đề KHÔNG phụ thuộc font: ưu tiên ảnh upload > SVG tĩnh > SVG emoji > ''."""

    def test_seeded_topics_use_static_svg(self):
        """Topic seed có icon_static → icon_src trỏ SVG tĩnh trong static (repo)."""
        t = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals',
                                 icon_static='icons/topic/animals.svg', icon='🐱')
        self.assertIn('icons/topic/animals.svg', t.icon_src)  # static() URL

    def test_uploaded_image_beats_static(self):
        """Có ảnh upload → ưu tiên hơn cả SVG tĩnh."""
        t = Topic.objects.create(
            name_en='X', name_vi='X', slug='x', icon_static='icons/topic/animals.svg',
            icon_image=SimpleUploadedFile('t.gif', GIF_1PX, content_type='image/gif'))
        self.assertIn('images/topic/', t.icon_src)  # media upload, không phải static

    def test_icon_src_empty_when_nothing_resolves(self):
        """Không ảnh + không static + emoji không có SVG offline → '' (fallback text)."""
        t = Topic.objects.create(name_en='Y', name_vi='Y', slug='y',
                                 icon_static='', icon='🫥')
        self.assertEqual(t.icon_src, '')


class ViNameAudioTests(TestCase):
    """
    Audio đọc TÊN tiếng Việt của từ (get_vi_name) cho game hình: bé chưa biết chữ
    chạm vào hình sẽ nghe tên. edge-tts được MOCK (không gọi mạng).
    """

    @classmethod
    def setUpTestData(cls):
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        cls.word = Word.objects.create(topic=cls.topic, text_en='cat', text_vi='con mèo')

    def setUp(self):
        # Cache audio vào thư mục tạm để không đụng media thật.
        self._tmp = tempfile.mkdtemp()
        self._override = self.settings(MEDIA_ROOT=self._tmp)
        self._override.enable()

    def tearDown(self):
        self._override.disable()

    def _fake_edge(self, text, out_path, voice):
        """Giả lập edge-tts: ghi file mp3 rỗng + nhớ text đã đọc (để khẳng định đọc text_vi)."""
        from pathlib import Path
        self._spoken = text
        Path(out_path).write_bytes(b'ID3')

    def test_get_vi_name_reads_text_vi_and_caches(self):
        """get_vi_name đọc CHỈ text_vi ('con mèo'), tạo file, và idempotent (lần 2 không gọi lại)."""
        from catalog import audio
        with mock.patch('catalog.audio.tts._edge_tts_save', side_effect=self._fake_edge) as m:
            url = audio.get_vi_name(self.word)
            self.assertTrue(url.endswith(f'names/name_{self.word.pk}.mp3'))
            self.assertEqual(self._spoken, 'con mèo')  # đọc đúng tên tiếng Việt, không câu dài
            # Lần 2: file đã có → KHÔNG gọi edge-tts lại (cache).
            audio.get_vi_name(self.word)
            self.assertEqual(m.call_count, 1)

    def test_get_vi_name_none_when_no_text_vi(self):
        """Từ không có text_vi → trả None (không sinh file rỗng)."""
        from catalog import audio
        w = Word.objects.create(topic=self.topic, text_en='x', text_vi='')
        self.assertIsNone(audio.get_vi_name(w))

    def test_word_payload_includes_vi_name_url(self):
        """word_payload gửi vi_name_url để game hình phát tên khi bé chạm hình."""
        from games.engine.base import word_payload
        with mock.patch('catalog.audio.tts._edge_tts_save', side_effect=self._fake_edge):
            payload = word_payload(self.word)
        self.assertIn('vi_name_url', payload)
        self.assertTrue(payload['vi_name_url'].endswith('.mp3'))
