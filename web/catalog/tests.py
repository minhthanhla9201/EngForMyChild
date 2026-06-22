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
        for name in ('topic_manage', 'topic_add', 'word_manage', 'word_add', 'word_import'):
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
