"""
Test khu catalog: model, view (login + nội dung), lệnh import CSV, audio (mock TTS).

TTS/IPA được MOCK — không gọi mạng/đọc loa thật, chỉ kiểm logic cache/idempotent.
"""

import io
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

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
