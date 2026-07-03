"""
Test khu trò chơi:
- Engine thuần (build_round/score_round + quy đổi sao) — không cần HTTP.
- View: login, lọc owner, submit chấm + lưu GameResult, thiếu từ → màn báo.
"""

import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import ChildProfile
from catalog.models import Topic, Word
from .engine import (
    image_pick_audio,
    listen_pick,
    listen_pick_image,
    match_image_audio,
    match_pairs,
)
from .engine.base import stars_from_ratio
from .models import GameResult, GameType


class EngineTests(TestCase):
    """Test luật chơi tách rời HTTP (nhanh, đúng tinh thần khuôn+dữ liệu)."""

    @classmethod
    def setUpTestData(cls):
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        cls.words = [Word.objects.create(topic=cls.topic, text_en=f'w{i}', text_vi=f'từ {i}')
                     for i in range(6)]

    def test_stars_thresholds(self):
        """Quy đổi sao đúng ngưỡng."""
        self.assertEqual(stars_from_ratio(10, 10), 3)
        self.assertEqual(stars_from_ratio(7, 10), 2)
        self.assertEqual(stars_from_ratio(4, 10), 1)
        self.assertEqual(stars_from_ratio(1, 10), 0)
        self.assertEqual(stars_from_ratio(0, 0), 0)  # không chia cho 0

    def test_listen_pick_build_round(self):
        """build_round tạo câu hỏi, mỗi câu 4 lựa chọn và có chứa đáp án."""
        data = listen_pick.build_round(self.words, count=3)
        self.assertEqual(len(data['questions']), 3)
        for q in data['questions']:
            self.assertEqual(len(q['choices']), 4)
            ids = [c['id'] for c in q['choices']]
            self.assertIn(q['answer_id'], ids)

    def test_listen_pick_score(self):
        """score_round chấm đúng số câu + sao."""
        payload = {'answers': [
            {'answer_id': 1, 'picked_id': 1},  # đúng
            {'answer_id': 2, 'picked_id': 9},  # sai
        ]}
        r = listen_pick.score_round(payload)
        self.assertEqual(r['score'], 1)
        self.assertEqual(r['total'], 2)

    def test_match_pairs_build_and_score(self):
        """build tạo 2 thẻ/cặp; score quy ra sao."""
        data = match_pairs.build_round(self.words, count=4)
        self.assertEqual(len(data['pairs']), 4)
        self.assertEqual(len(data['cards']), 8)  # 4 cặp × 2 mặt
        r = match_pairs.score_round({'pairs_total': 4, 'pairs_matched': 4, 'mistakes': 0})
        self.assertEqual(r['stars'], 3)

    def test_listen_pick_image_build_and_score(self):
        """Nghe & chọn hình: cùng cấu trúc listen_pick, choice có trường image."""
        data = listen_pick_image.build_round(self.words, count=3)
        self.assertEqual(len(data['questions']), 3)
        for q in data['questions']:
            self.assertEqual(len(q['choices']), 4)
            self.assertIn(q['answer_id'], [c['id'] for c in q['choices']])
            self.assertIn('image', q['choices'][0])  # có trường hình cho bé chọn
        r = listen_pick_image.score_round(
            {'answers': [{'answer_id': 1, 'picked_id': 1}, {'answer_id': 2, 'picked_id': 9}]})
        self.assertEqual(r['score'], 1)
        self.assertEqual(r['total'], 2)

    def test_image_pick_audio_build_and_score(self):
        """Nhìn hình & chọn tiếng: mỗi câu có image_word_id + URL hình + 4 audio."""
        # Từ CÓ ảnh để kiểm URL hình đáp án (game này hiện hình → cần ảnh thật).
        worded = [Word.objects.create(topic=self.topic, text_en=f'p{i}', text_vi=f'q{i}',
                                      image=f'images/p{i}.png') for i in range(5)]
        data = image_pick_audio.build_round(worded, count=3)
        self.assertEqual(len(data['questions']), 3)
        for q in data['questions']:
            self.assertEqual(len(q['choices']), 4)
            self.assertIn('image_word_id', q)
            self.assertIn(q['answer_id'], [c['id'] for c in q['choices']])
            # Câu hỏi PHẢI có URL hình của đáp án (bug cũ: thiếu → <img> src rỗng).
            self.assertTrue(q['image'], 'câu hỏi thiếu URL hình đáp án')
            answer = next(c for c in q['choices'] if c['id'] == q['answer_id'])
            self.assertEqual(q['image'], answer['image'])  # hình đúng của đáp án
        r = image_pick_audio.score_round(
            {'answers': [{'answer_id': 1, 'picked_id': 1}, {'answer_id': 2, 'picked_id': 2}]})
        self.assertEqual(r['score'], 2)
        self.assertEqual(r['stars'], 3)

    def test_match_image_audio_build_and_score(self):
        """Ghép hình với tiếng: mỗi cặp có thẻ face='image' và thẻ face='audio'."""
        data = match_image_audio.build_round(self.words, count=4)
        self.assertEqual(len(data['pairs']), 4)
        self.assertEqual(len(data['cards']), 8)  # 4 cặp × 2 mặt (hình + loa)
        faces = {c['face'] for c in data['cards']}
        self.assertEqual(faces, {'image', 'audio'})
        for c in data['cards']:
            self.assertIn('word_id', c)  # để client gọi API audio
        r = match_image_audio.score_round({'pairs_total': 4, 'pairs_matched': 4, 'mistakes': 0})
        self.assertEqual(r['stars'], 3)


class GamesViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')
        cls.other = User.objects.create_user('other', password='pass12345')
        cls.child = ChildProfile.objects.create(owner=cls.parent, name='Bi')
        cls.other_child = ChildProfile.objects.create(owner=cls.other, name='Bo')
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        for i in range(6):
            Word.objects.create(topic=cls.topic, text_en=f'w{i}', text_vi=f'từ {i}')
        # GameType có sẵn từ migration seed.
        cls.game = GameType.objects.get(code='listen-pick')

    def test_choose_requires_login(self):
        resp = self.client.get(reverse('games:choose'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), resp.url)

    def test_play_loads_for_own_child(self):
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('games:play', args=[self.child.pk, 'listen-pick', 'animals']))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'round-data')

    def test_play_shows_hint_and_voice_url(self):
        """Màn chơi hiện câu hướng dẫn (hint_vi) + nhúng hint-url để phát giọng."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('games:play', args=[self.child.pk, 'listen-pick', 'animals']))
        # Câu hướng dẫn của game hiện trong màn (từ GameType.hint_vi seed).
        self.assertContains(resp, self.game.hint_vi)
        # Có phần tử hint-url để JS phát giọng (rỗng nếu chưa sinh mp3 — vẫn phải có thẻ).
        self.assertContains(resp, 'hint-url')

    def test_round_data_is_object_not_double_encoded(self):
        """
        json_script phải nhúng round_data thành OBJECT, không phải chuỗi JSON lồng.
        (Bắt lỗi double-encoding: view json.dumps + template json_script → client nhận str.)
        """
        import html
        import re
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('games:play', args=[self.child.pk, 'listen-pick', 'animals']))
        m = re.search(r'id="round-data"[^>]*>(.*?)</script>', resp.content.decode(), re.S)
        data = json.loads(html.unescape(m.group(1)))
        self.assertIsInstance(data, dict)            # phải là object, KHÔNG phải str
        self.assertIn('questions', data)
        self.assertTrue(all(len(q['choices']) == 4 for q in data['questions']))

    def test_play_blocked_for_other_child(self):
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('games:play', args=[self.other_child.pk, 'listen-pick', 'animals']))
        self.assertEqual(resp.status_code, 404)

    def test_submit_saves_result(self):
        """POST kết quả → chấm + lưu GameResult gắn đúng bé/game/chủ đề."""
        self.client.login(username='parent', password='pass12345')
        url = reverse('games:submit', args=[self.child.pk, 'listen-pick', 'animals'])
        body = json.dumps({'answers': [{'answer_id': 1, 'picked_id': 1}], 'duration_sec': 12})
        resp = self.client.post(url, body, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['ok'])
        gr = GameResult.objects.get(child=self.child, game_type=self.game)
        self.assertEqual(gr.topic, self.topic)
        self.assertEqual(gr.total, 1)
        self.assertEqual(gr.duration_sec, 12)

    def test_play_empty_when_not_enough_words(self):
        """Chủ đề thiếu từ → màn báo (không lỗi)."""
        empty_topic = Topic.objects.create(name_en='Empty', name_vi='Rỗng', slug='empty')
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('games:play', args=[self.child.pk, 'listen-pick', 'empty']))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'chưa đủ từ')

    def test_recognition_games_need_words_with_image(self):
        """
        Game nhận dạng (needs_image='Y') chỉ dùng từ có ảnh: chủ đề toàn từ không
        ảnh → màn báo; khi có đủ từ có ảnh → chơi được.
        """
        self.client.login(username='parent', password='pass12345')
        # Chủ đề hiện tại (6 từ, đều KHÔNG ảnh) → thiếu từ có ảnh.
        resp = self.client.get(
            reverse('games:play', args=[self.child.pk, 'listen-pick-image', 'animals']))
        self.assertContains(resp, 'chưa đủ từ')

        # Chủ đề mới đủ 4 từ CÓ ảnh → chơi được cả 3 game nhận dạng.
        topic = Topic.objects.create(name_en='Fruit', name_vi='Trái cây', slug='fruit')
        for i in range(4):
            Word.objects.create(topic=topic, text_en=f'f{i}', text_vi=f'quả {i}',
                                image=f'images/f{i}.png')
        for code in ('listen-pick-image', 'image-pick-audio', 'match-image-audio'):
            resp = self.client.get(reverse('games:play', args=[self.child.pk, code, 'fruit']))
            self.assertEqual(resp.status_code, 200, code)
            self.assertContains(resp, 'round-data', msg_prefix=code)
