"""
Test tiến độ & huy hiệu:
- Service: đếm chỉ số, mốc linh vật, streak, mở khoá badge (idempotent, đúng ngưỡng).
- View trang chủ khu bé: login, chọn bé (session), hiện tiến độ; lọc owner.
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import ChildProfile
from accounts.tests import ManageTestMixin
from catalog.models import Topic, Word
from core.icons import emoji_to_filename
from games.models import GameResult, GameType
from pronunciation.models import Attempt
from . import service
from .models import Badge, ChildBadge, PetStage

# GIF 1x1 hợp lệ để test upload ImageField (Pillow đọc được).
GIF_1PX = (b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!'
           b'\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;')


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


class IconResolutionTests(TestCase):
    """Icon không phụ thuộc font: icon_src ưu tiên ảnh upload > SVG tĩnh > SVG emoji > ''."""

    def test_emoji_to_filename_matches_twemoji_convention(self):
        """Khớp quy ước cũ của fetch_images: HOA, nối '-', bỏ FE0F."""
        self.assertEqual(emoji_to_filename('🐱'), '1F431')
        self.assertEqual(emoji_to_filename('☂️'), '2602')  # bỏ VS16 (FE0F)

    def test_seeded_petstage_uses_static_svg(self):
        """Linh vật đã seed có icon_static → icon_src trỏ SVG tĩnh trong static (repo)."""
        stage = PetStage.objects.get(threshold=50)
        self.assertEqual(stage.icon_static, 'icons/pet/tree.svg')
        self.assertIn('icons/pet/tree.svg', stage.icon_src)  # static() prefix + path

    def test_seeded_badge_uses_static_svg(self):
        """Huy hiệu đã seed có icon_static → icon_src trỏ SVG tĩnh."""
        badge = Badge.objects.get(code='stars-10')
        self.assertEqual(badge.icon_static, 'icons/badge/stars-10.svg')
        self.assertIn('icons/badge/stars-10.svg', badge.icon_src)

    def test_uploaded_image_beats_static(self):
        """Có ảnh upload → ưu tiên hơn cả SVG tĩnh."""
        stage = PetStage.objects.create(
            threshold=999, name_vi='Test', icon_static='icons/pet/tree.svg', emoji='🌱',
            image=SimpleUploadedFile('p.gif', GIF_1PX, content_type='image/gif'))
        self.assertIn('images/pet/', stage.icon_src)  # media upload, không phải static

    def test_icon_src_empty_when_nothing_set(self):
        """Không ảnh + không static + emoji không có SVG offline → '' (fallback text)."""
        badge = Badge.objects.create(code='zzz', name_vi='X', icon='🫥',
                                     icon_static='', kind='STARS', threshold=1)
        self.assertEqual(badge.icon_src, '')


class PetStageEmptyFallbackTests(TestCase):
    """Bảng PetStage rỗng → service không vỡ, dùng mốc mặc định."""

    def test_summary_without_stages(self):
        PetStage.objects.all().delete()  # xoá mốc seed
        parent = User.objects.create_user('p', password='x12345678')
        child = ChildProfile.objects.create(owner=parent, name='Bi')
        s = service.summary(child)
        self.assertEqual(s['pet_name'], 'Hạt mầm')
        self.assertEqual(s['pet_icon_src'], '')  # không có object → fallback text


@override_settings(MEDIA_ROOT=__import__('tempfile').mkdtemp())
class ManagePetStageBadgeTests(ManageTestMixin, TestCase):
    """CRUD linh vật & huy hiệu ở khu quản lý: cần mở khoá; tạo/sửa lưu đúng."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')

    def test_petstage_manage_requires_unlock(self):
        """Chưa mở khoá passcode → chặn (redirect unlock)."""
        self.login()
        self.set_passcode()
        resp = self.client.get(reverse('progress_manage:petstage_manage'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:manage_unlock'), resp.url)

    def test_petstage_add(self):
        """POST tạo mốc linh vật mới (kèm upload ảnh) lưu đúng."""
        self.unlock_manage()
        resp = self.client.post(reverse('progress_manage:petstage_add'), {
            'threshold': 500, 'name_vi': 'Cây thần', 'emoji': '🌲', 'order': 9, 'active': 'Y',
            'image': SimpleUploadedFile('p.gif', GIF_1PX, content_type='image/gif'),
        })
        self.assertEqual(resp.status_code, 302)
        stage = PetStage.objects.get(threshold=500)
        self.assertEqual(stage.name_vi, 'Cây thần')
        self.assertTrue(stage.image)

    def test_badge_add(self):
        """POST tạo huy hiệu mới lưu đúng."""
        self.unlock_manage()
        resp = self.client.post(reverse('progress_manage:badge_add'), {
            'code': 'test-badge', 'name_vi': 'Huy hiệu test', 'icon': '🎖️', 'desc_vi': 'Giỏi',
            'kind': 'STARS', 'threshold': 5, 'order': 20, 'active': 'Y',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Badge.objects.filter(code='test-badge', threshold=5).exists())

    def test_petstage_edit(self):
        """Sửa mốc linh vật đã seed."""
        self.unlock_manage()
        stage = PetStage.objects.get(threshold=10)
        resp = self.client.post(reverse('progress_manage:petstage_edit', args=[stage.pk]), {
            'threshold': 10, 'name_vi': 'Chồi xanh', 'emoji': '🌿', 'order': 2, 'active': 'Y',
        })
        self.assertEqual(resp.status_code, 302)
        stage.refresh_from_db()
        self.assertEqual(stage.name_vi, 'Chồi xanh')
