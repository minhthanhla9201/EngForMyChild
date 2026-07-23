"""
Test khu luyện phát âm: yêu cầu đăng nhập, lọc owner, lưu bản ghi (Attempt),
và ràng buộc POST-only cho API lưu.
"""

import shutil
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import ChildProfile
from catalog.models import Topic, Word
from . import asr as asr_service
from .models import Attempt

# Ghi file test vào thư mục tạm rồi xoá — không để rác trong media/ thật.
_TMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=_TMP_MEDIA)
class PronunciationViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')
        cls.other = User.objects.create_user('other', password='pass12345')
        cls.child = ChildProfile.objects.create(owner=cls.parent, name='Bi')
        cls.other_child = ChildProfile.objects.create(owner=cls.other, name='Bo')
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        cls.word = Word.objects.create(topic=cls.topic, text_en='cat', text_vi='con mèo')

    @classmethod
    def tearDownClass(cls):
        # Dọn thư mục media tạm sau khi chạy xong.
        shutil.rmtree(_TMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def test_choose_requires_login(self):
        """Chưa đăng nhập → redirect login."""
        resp = self.client.get(reverse('pronunciation:choose'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), resp.url)

    def test_practice_page_loads_for_own_child(self):
        """Đăng nhập + bé của mình → màn luyện hiện từ."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('pronunciation:practice', args=[self.child.pk, 'animals']))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'cat')

    def test_words_data_is_list_not_double_encoded(self):
        """words-data phải là LIST object (bắt lỗi double-encoding json.dumps + json_script)."""
        import html
        import json
        import re
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('pronunciation:practice', args=[self.child.pk, 'animals']))
        m = re.search(r'id="words-data"[^>]*>(.*?)</script>', resp.content.decode(), re.S)
        data = json.loads(html.unescape(m.group(1)))
        self.assertIsInstance(data, list)
        self.assertTrue(all('text_en' in w for w in data))

    def test_words_data_maps_real_image_per_word(self):
        """
        Mỗi từ phải mang ĐÚNG ảnh của chính nó (image = w.image.url), từ chưa có
        ảnh thì rỗng — không dùng chung một icon cứng cho mọi từ.
        """
        import html
        import json
        import re
        # Thêm 1 từ CÓ ảnh + đảm bảo 'cat' (không ảnh) vẫn rỗng.
        Word.objects.create(topic=self.topic, text_en='dog', text_vi='con chó',
                            image='images/dog.png')
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('pronunciation:practice', args=[self.child.pk, 'animals']))
        m = re.search(r'id="words-data"[^>]*>(.*?)</script>', resp.content.decode(), re.S)
        data = json.loads(html.unescape(m.group(1)))
        by_en = {w['text_en']: w for w in data}
        self.assertIn('image', by_en['dog'])
        self.assertTrue(by_en['dog']['image'].endswith('images/dog.png'))  # ảnh đúng của 'dog'
        self.assertEqual(by_en['cat']['image'], '')                        # 'cat' chưa có ảnh

    def test_practice_blocked_for_other_child(self):
        """Không luyện được trên bé của phụ huynh khác → 404."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('pronunciation:practice', args=[self.other_child.pk, 'animals']))
        self.assertEqual(resp.status_code, 404)

    @mock.patch('pronunciation.views.asr_service.score',
                return_value={'heard': 'cat', 'target': 'cat', 'score': 100, 'stars': 3})
    def test_save_attempt_scores_recording(self, _mock):
        """POST bản ghi → chấm điểm (ASR mock) → điền stars/asr_text, trả kết quả."""
        self.client.login(username='parent', password='pass12345')
        audio = SimpleUploadedFile('rec.webm', b'fake-audio-bytes', content_type='audio/webm')
        url = reverse('pronunciation:save_attempt', args=[self.child.pk, self.word.pk])
        resp = self.client.post(url, {'audio': audio})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['ok'])
        self.assertTrue(data['scored'])
        self.assertEqual(data['stars'], 3)
        attempt = Attempt.objects.get(child=self.child, word=self.word)
        self.assertTrue(attempt.recording.name)
        self.assertTrue(attempt.is_scored)          # đã chấm
        self.assertEqual(attempt.stars, 3)
        self.assertEqual(attempt.asr_text, 'cat')

    @mock.patch('pronunciation.views.asr_service.score', return_value=None)
    def test_save_attempt_when_asr_off(self, _mock):
        """ASR tắt/lỗi (score None) → vẫn lưu bản ghi, KHÔNG chấm, không 500."""
        self.client.login(username='parent', password='pass12345')
        audio = SimpleUploadedFile('rec.webm', b'x', content_type='audio/webm')
        url = reverse('pronunciation:save_attempt', args=[self.child.pk, self.word.pk])
        resp = self.client.post(url, {'audio': audio})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['ok'])
        self.assertFalse(data['scored'])            # không chấm được
        attempt = Attempt.objects.get(child=self.child, word=self.word)
        self.assertFalse(attempt.is_scored)         # để trống, chờ lần sau

    def test_save_attempt_requires_post(self):
        """GET vào API lưu → 405 (chỉ nhận POST)."""
        self.client.login(username='parent', password='pass12345')
        url = reverse('pronunciation:save_attempt', args=[self.child.pk, self.word.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

    def test_save_attempt_missing_audio(self):
        """POST thiếu file audio → 400, không tạo Attempt."""
        self.client.login(username='parent', password='pass12345')
        url = reverse('pronunciation:save_attempt', args=[self.child.pk, self.word.pk])
        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Attempt.objects.count(), 0)

    def test_save_attempt_blocked_for_other_child(self):
        """Không lưu được bản ghi vào bé của người khác → 404."""
        self.client.login(username='parent', password='pass12345')
        audio = SimpleUploadedFile('rec.webm', b'x', content_type='audio/webm')
        url = reverse('pronunciation:save_attempt', args=[self.other_child.pk, self.word.pk])
        resp = self.client.post(url, {'audio': audio})
        self.assertEqual(resp.status_code, 404)


class AsrScoringTests(TestCase):
    """Chấm phát âm — logic thuần (so khớp + quy sao), không gọi service thật."""

    def test_match_score_exact_and_partial(self):
        """Khớp hoàn toàn = 100 (bỏ hoa/dấu câu); lệch thì thấp hơn."""
        self.assertEqual(asr_service.match_score('cat', 'cat'), 100)
        self.assertEqual(asr_service.match_score('Cat.', 'cat'), 100)   # chuẩn hoá
        self.assertTrue(asr_service.match_score('cut', 'cat') < 100)
        self.assertEqual(asr_service.match_score('', 'cat'), 0)

    def test_stars_thresholds(self):
        """Quy điểm khớp → sao theo ngưỡng khích lệ mới (5 sao)."""
        self.assertEqual(asr_service.stars_from_score(100), 5)
        self.assertEqual(asr_service.stars_from_score(95), 4)
        self.assertEqual(asr_service.stars_from_score(80), 3)
        self.assertEqual(asr_service.stars_from_score(60), 2)
        self.assertEqual(asr_service.stars_from_score(40), 1)
        self.assertEqual(asr_service.stars_from_score(10), 0)

    def test_transcribe_returns_none_when_asr_down(self):
        """ASR không gọi được → transcribe trả None (không raise)."""
        with mock.patch('pronunciation.asr.requests.post', side_effect=Exception('down')):
            self.assertIsNone(asr_service.transcribe(
                SimpleUploadedFile('r.webm', b'x', content_type='audio/webm')))

    def test_score_combines_transcribe_and_match(self):
        """score() ghép transcribe + match → dict có heard/score/stars."""
        with mock.patch('pronunciation.asr.transcribe', return_value='cat'):
            r = asr_service.score(SimpleUploadedFile('r.webm', b'x'), 'cat')
        self.assertEqual(r['heard'], 'cat')
        self.assertEqual(r['stars'], 5)
