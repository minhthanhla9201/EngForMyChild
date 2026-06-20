"""
Test khu luyện phát âm: yêu cầu đăng nhập, lọc owner, lưu bản ghi (Attempt),
và ràng buộc POST-only cho API lưu.
"""

import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import ChildProfile
from catalog.models import Topic, Word
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

    def test_practice_blocked_for_other_child(self):
        """Không luyện được trên bé của phụ huynh khác → 404."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('pronunciation:practice', args=[self.other_child.pk, 'animals']))
        self.assertEqual(resp.status_code, 404)

    def test_save_attempt_creates_record(self):
        """POST bản ghi → tạo Attempt gắn đúng bé + từ."""
        self.client.login(username='parent', password='pass12345')
        audio = SimpleUploadedFile('rec.webm', b'fake-audio-bytes', content_type='audio/webm')
        url = reverse('pronunciation:save_attempt', args=[self.child.pk, self.word.pk])
        resp = self.client.post(url, {'audio': audio})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['ok'])
        attempt = Attempt.objects.get(child=self.child, word=self.word)
        self.assertTrue(attempt.recording.name)
        self.assertFalse(attempt.is_scored)  # GĐ 2 chưa chấm điểm

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
