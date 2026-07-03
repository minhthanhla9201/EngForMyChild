"""
Test tiến độ & huy hiệu:
- Service: đếm chỉ số, mốc linh vật, streak, mở khoá badge (idempotent, đúng ngưỡng).
- View trang chủ khu bé: login, chọn bé (session), hiện tiến độ; lọc owner.
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import ChildProfile
from catalog.models import Topic, Word
from games.models import GameResult, GameType
from pronunciation.models import Attempt
from . import service
from .models import Badge, ChildBadge


class ProgressServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')
        cls.child = ChildProfile.objects.create(owner=cls.parent, name='Bi')
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        cls.word = Word.objects.create(topic=cls.topic, text_en='cat', text_vi='con mèo')
        cls.game = GameType.objects.get(code='listen-pick')  # seed sẵn

    def test_pet_stage_thresholds(self):
        """Linh vật lớn dần theo tổng sao (chọn mốc cao nhất đạt được)."""
        self.assertEqual(service.pet_stage(0)[2], 'Hạt mầm')
        self.assertEqual(service.pet_stage(10)[2], 'Chồi non')
        self.assertEqual(service.pet_stage(60)[2], 'Cây lớn')
        self.assertEqual(service.pet_stage(9)[2], 'Hạt mầm')  # chưa đủ 10

    def test_summary_counts(self):
        """summary đếm đúng sao/lượt chơi/lần luyện."""
        GameResult.objects.create(child=self.child, game_type=self.game, topic=self.topic,
                                  stars=3, score=3, total=3)
        GameResult.objects.create(child=self.child, game_type=self.game, topic=self.topic,
                                  stars=2, score=2, total=3)
        Attempt.objects.create(child=self.child, word=self.word, recording='recordings/a.webm')
        s = service.summary(self.child)
        self.assertEqual(s['total_stars'], 5)
        self.assertEqual(s['games_played'], 2)
        self.assertEqual(s['words_practiced'], 1)

    def test_award_badges_by_stars_idempotent(self):
        """Đủ ngưỡng sao → mở huy hiệu; gọi lại không trao trùng."""
        GameResult.objects.create(child=self.child, game_type=self.game, topic=self.topic,
                                  stars=3, score=3, total=3)
        new1 = service.check_and_award_badges(self.child)
        codes = {b.code for b in new1}
        self.assertIn('first-star', codes)   # >=1 sao
        self.assertNotIn('stars-10', codes)  # chưa đủ 10
        # Gọi lại: không trao thêm huy hiệu cũ.
        new2 = service.check_and_award_badges(self.child)
        self.assertEqual(new2, [])
        # Tổng số ChildBadge không tăng khi chạy lại.
        cnt = ChildBadge.objects.filter(child=self.child).count()
        service.check_and_award_badges(self.child)
        self.assertEqual(ChildBadge.objects.filter(child=self.child).count(), cnt)

    def test_award_first_word_on_attempt(self):
        """Luyện 1 từ → mở huy hiệu 'Tập nói'."""
        Attempt.objects.create(child=self.child, word=self.word, recording='recordings/a.webm')
        new = service.check_and_award_badges(self.child)
        self.assertIn('first-word', {b.code for b in new})

    def test_streak_counts_consecutive_days(self):
        """Streak đếm số ngày liên tiếp có hoạt động tính đến hôm nay."""
        today = timezone.now()
        # Hoạt động hôm nay và hôm qua → streak 2.
        a1 = Attempt.objects.create(child=self.child, word=self.word, recording='recordings/1.webm')
        a2 = Attempt.objects.create(child=self.child, word=self.word, recording='recordings/2.webm')
        # Ép created_at hôm qua cho a2 (auto_now_add nên phải update thẳng).
        Attempt.objects.filter(pk=a2.pk).update(created_at=today - timedelta(days=1))
        self.assertEqual(service._streak_days(self.child), 2)


class KidHomeViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')
        cls.other = User.objects.create_user('other', password='pass12345')
        cls.child = ChildProfile.objects.create(owner=cls.parent, name='Bi', avatar='🐥')
        cls.child2 = ChildProfile.objects.create(owner=cls.parent, name='Bo')
        cls.other_child = ChildProfile.objects.create(owner=cls.other, name='Bin')

    def test_home_requires_login(self):
        resp = self.client.get(reverse('accounts:home'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), resp.url)

    def test_home_shows_child_picker_when_multiple(self):
        """Nhiều bé, chưa chọn → hiện màn chọn bé (avatar)."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('accounts:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Bé nào đang học')
        self.assertContains(resp, 'Bi')

    def test_select_child_then_show_progress(self):
        """Chọn bé → lưu session → trang chủ hiện tiến độ (linh vật, sao)."""
        self.client.login(username='parent', password='pass12345')
        self.client.get(reverse('accounts:set_active_child', args=[self.child.pk]))
        resp = self.client.get(reverse('accounts:home'))
        self.assertContains(resp, 'Chào')
        self.assertContains(resp, 'Tổng số sao')
        self.assertContains(resp, 'Huy hiệu')

    def test_cannot_select_other_parents_child(self):
        """Không chọn được bé của phụ huynh khác → 404."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('accounts:set_active_child', args=[self.other_child.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_switch_clears_active_child(self):
        """?switch=1 → xoá bé đang chọn, quay lại màn chọn."""
        self.client.login(username='parent', password='pass12345')
        self.client.get(reverse('accounts:set_active_child', args=[self.child.pk]))
        resp = self.client.get(reverse('accounts:home') + '?switch=1', follow=True)
        self.assertContains(resp, 'Bé nào đang học')
