"""
Test khu tài khoản: đăng nhập, trang chủ bé, luồng passcode khu quản lý,
và các view quản lý (lọc owner). Khu quản lý cần đăng nhập + mở khoá passcode.
"""

import tempfile

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Topic, Word
from games.models import GameResult, GameType
from pronunciation.models import Attempt

from .models import ChildProfile, ManagePasscode

PASSCODE = '4321'


class ManageTestMixin:
    """Tiện ích: đăng nhập + đặt passcode + mở khoá khu quản lý cho test."""

    def login(self, username='parent', password='pass12345'):
        self.client.login(username=username, password=password)

    def set_passcode(self, raw=PASSCODE):
        pc = ManagePasscode.get_solo()
        pc.set_passcode(raw)
        return pc

    def unlock_manage(self):
        """Đăng nhập rồi nhập passcode đúng để mở khoá (qua đúng view, sát thực tế)."""
        self.login()
        self.set_passcode()
        self.client.post(reverse('accounts:manage_unlock'), {'passcode': PASSCODE})


class KidHomeTests(TestCase):
    """Trang chủ khu của bé: cần đăng nhập, hiện 3 hoạt động."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')

    def test_home_requires_login(self):
        resp = self.client.get(reverse('accounts:home'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), resp.url)

    def test_home_shows_activities(self):
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('accounts:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Học từ vựng')
        self.assertContains(resp, 'Luyện phát âm')
        self.assertContains(resp, 'Trò chơi')
        # KHÔNG lộ menu/nút khu quản lý trên trang của bé.
        self.assertNotContains(resp, 'Thoát')


class ManagePasscodeFlowTests(ManageTestMixin, TestCase):
    """Luồng passcode: đặt lần đầu, nhập đúng/sai, hết hạn, đổi passcode."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')

    def test_unlock_requires_login(self):
        resp = self.client.get(reverse('accounts:manage_unlock'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), resp.url)

    def test_first_time_shows_set_passcode(self):
        """Chưa có passcode → màn ĐẶT passcode lần đầu."""
        self.login()
        resp = self.client.get(reverse('accounts:manage_unlock'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Đặt passcode')

    def test_set_passcode_then_unlocked(self):
        """Đặt passcode lần đầu → lưu hash + mở khoá luôn → vào dashboard được."""
        self.login()
        resp = self.client.post(reverse('accounts:manage_unlock'),
                                {'passcode1': PASSCODE, 'passcode2': PASSCODE})
        self.assertRedirects(resp, reverse('accounts:dashboard'))
        self.assertTrue(ManagePasscode.get_solo().is_set)
        # Đã mở khoá → dashboard 200.
        self.assertEqual(self.client.get(reverse('accounts:dashboard')).status_code, 200)

    def test_set_passcode_mismatch(self):
        self.login()
        resp = self.client.post(reverse('accounts:manage_unlock'),
                                {'passcode1': '4321', 'passcode2': '9999'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'khớp')
        self.assertFalse(ManagePasscode.get_solo().is_set)

    def test_unlock_wrong_passcode(self):
        self.login()
        self.set_passcode()
        resp = self.client.post(reverse('accounts:manage_unlock'), {'passcode': '0000'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'chưa đúng')
        # Chưa mở khoá → vào dashboard vẫn bị chặn về unlock.
        self.assertIn(reverse('accounts:manage_unlock'),
                      self.client.get(reverse('accounts:dashboard')).url)

    def test_unlock_correct_then_access(self):
        self.login()
        self.set_passcode()
        resp = self.client.post(reverse('accounts:manage_unlock'), {'passcode': PASSCODE})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.client.get(reverse('accounts:dashboard')).status_code, 200)

    def test_unlock_expires(self):
        """Quá hạn (sửa mốc mở khoá về quá khứ) → bị chặn lại về màn nhập passcode."""
        self.unlock_manage()
        # Đẩy mốc mở khoá lùi 999 phút trong session → quá hạn.
        from core.decorators import SESSION_KEY
        from django.utils import timezone
        from datetime import timedelta
        s = self.client.session
        s[SESSION_KEY] = (timezone.now() - timedelta(minutes=999)).isoformat()
        s.save()
        resp = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:manage_unlock'), resp.url)

    def test_lock_clears_unlock(self):
        """Bấm "Về khu của bé" (lock) → khoá lại, vào dashboard phải nhập passcode."""
        self.unlock_manage()
        resp = self.client.get(reverse('accounts:manage_lock'))
        self.assertRedirects(resp, reverse('accounts:home'))
        self.assertIn(reverse('accounts:manage_unlock'),
                      self.client.get(reverse('accounts:dashboard')).url)

    def test_change_passcode(self):
        self.unlock_manage()
        resp = self.client.post(reverse('accounts:manage_passcode_change'),
                                {'current': PASSCODE, 'passcode1': '5678', 'passcode2': '5678'})
        self.assertRedirects(resp, reverse('accounts:dashboard'))
        self.assertTrue(ManagePasscode.get_solo().check_passcode('5678'))

    def test_change_passcode_wrong_current(self):
        self.unlock_manage()
        resp = self.client.post(reverse('accounts:manage_passcode_change'),
                                {'current': '0000', 'passcode1': '5678', 'passcode2': '5678'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'hiện tại chưa đúng')


class DashboardTests(ManageTestMixin, TestCase):
    """Bảng điều khiển khu quản lý: cần mở khoá; hiện số liệu + hồ sơ bé của owner."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')
        cls.other = User.objects.create_user('other', password='pass12345')
        cls.child = ChildProfile.objects.create(owner=cls.parent, name='Bi')
        cls.other_child = ChildProfile.objects.create(owner=cls.other, name='Bo')
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        Word.objects.create(topic=cls.topic, text_en='cat', text_vi='con mèo')

    def test_dashboard_requires_unlock(self):
        """Đăng nhập nhưng chưa mở khoá → chặn về màn nhập passcode."""
        self.login()
        self.set_passcode()
        resp = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:manage_unlock'), resp.url)

    def test_dashboard_shows_stats_and_own_children(self):
        self.unlock_manage()
        resp = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['stats'], {'children': 1, 'topics': 1, 'words': 1})
        self.assertContains(resp, 'Bi')
        self.assertNotContains(resp, 'Bo')


class ChildProfileViewTests(ManageTestMixin, TestCase):
    """CRUD hồ sơ bé (trong khu quản lý): cần mở khoá, lọc owner."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')
        cls.other = User.objects.create_user('other', password='pass12345')
        cls.other_child = ChildProfile.objects.create(owner=cls.other, name='Bo')

    def test_child_add_requires_unlock(self):
        self.login()
        self.set_passcode()
        resp = self.client.get(reverse('accounts:child_add'))
        self.assertIn(reverse('accounts:manage_unlock'), resp.url)

    def test_add_child_sets_owner_and_audit(self):
        self.unlock_manage()
        resp = self.client.post(reverse('accounts:child_add'),
                                {'name': 'Na', 'birth_year': 2018, 'avatar': '🐥'})
        self.assertRedirects(resp, reverse('accounts:dashboard'))
        child = ChildProfile.objects.get(name='Na')
        self.assertEqual(child.owner, self.parent)
        self.assertEqual(child.created_by, self.parent)

    def test_cannot_edit_other_parent_child(self):
        self.unlock_manage()
        resp = self.client.get(reverse('accounts:child_edit', args=[self.other_child.pk]))
        self.assertEqual(resp.status_code, 404)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ChildDeleteTests(ManageTestMixin, TestCase):
    """Xoá hồ sơ bé + toàn bộ dữ liệu liên quan (Attempt/GameResult) + dọn file ghi âm.

    MEDIA_ROOT trỏ thư mục tạm để test file ghi âm không rác vào media/ thật.
    """

    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')
        cls.other = User.objects.create_user('other', password='pass12345')
        cls.other_child = ChildProfile.objects.create(owner=cls.other, name='Bo')
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        cls.word = Word.objects.create(topic=cls.topic, text_en='cat', text_vi='con mèo')
        cls.game, _ = GameType.objects.get_or_create(
            code='listen-pick', defaults={'name_vi': 'Nghe chọn', 'module': 'listen_pick'})

    def _make_child_with_data(self):
        """Tạo 1 bé của parent kèm 1 Attempt (có file ghi âm) + 1 GameResult."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        child = ChildProfile.objects.create(owner=self.parent, name='Bi')
        rec = SimpleUploadedFile('r.wav', b'RIFFxxxx', content_type='audio/wav')
        attempt = Attempt.objects.create(child=child, word=self.word, recording=rec)
        GameResult.objects.create(child=child, game_type=self.game, topic=self.topic,
                                  stars=3, score=4, total=4)
        return child, attempt

    def test_delete_requires_unlock(self):
        self.login()
        self.set_passcode()
        child, _ = self._make_child_with_data()
        resp = self.client.post(reverse('accounts:child_delete', args=[child.pk]),
                                {'confirm_name': 'Bi'})
        self.assertIn(reverse('accounts:manage_unlock'), resp.url)
        self.assertTrue(ChildProfile.objects.filter(pk=child.pk).exists())

    def test_cannot_delete_other_parent_child(self):
        self.unlock_manage()
        resp = self.client.post(reverse('accounts:child_delete', args=[self.other_child.pk]),
                                {'confirm_name': 'Bo'})
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(ChildProfile.objects.filter(pk=self.other_child.pk).exists())

    def test_get_does_not_delete(self):
        """GET không xoá (thao tác thay đổi dữ liệu chỉ nhận POST)."""
        self.unlock_manage()
        child, _ = self._make_child_with_data()
        resp = self.client.get(reverse('accounts:child_delete', args=[child.pk]))
        self.assertRedirects(resp, reverse('accounts:child_edit', args=[child.pk]))
        self.assertTrue(ChildProfile.objects.filter(pk=child.pk).exists())

    def test_wrong_confirm_name_does_not_delete(self):
        self.unlock_manage()
        child, _ = self._make_child_with_data()
        resp = self.client.post(reverse('accounts:child_delete', args=[child.pk]),
                                {'confirm_name': 'sai-ten'})
        self.assertRedirects(resp, reverse('accounts:child_edit', args=[child.pk]))
        self.assertTrue(ChildProfile.objects.filter(pk=child.pk).exists())

    def test_delete_removes_child_and_related_data_and_file(self):
        """Xác nhận đúng tên → xoá bé + Attempt + GameResult (cascade) + file ghi âm trên đĩa."""
        import os
        self.unlock_manage()
        child, attempt = self._make_child_with_data()
        file_path = attempt.recording.path
        self.assertTrue(os.path.exists(file_path))

        resp = self.client.post(reverse('accounts:child_delete', args=[child.pk]),
                                {'confirm_name': 'Bi'})
        self.assertRedirects(resp, reverse('accounts:dashboard'))
        self.assertFalse(ChildProfile.objects.filter(pk=child.pk).exists())
        # Dữ liệu liên quan bị xoá theo (cascade).
        self.assertEqual(Attempt.objects.filter(child=child).count(), 0)
        self.assertEqual(GameResult.objects.filter(child=child).count(), 0)
        # File ghi âm được dọn khỏi đĩa.
        self.assertFalse(os.path.exists(file_path))


class LoginViewTests(TestCase):
    """Kiểm chứng luồng đăng nhập qua trang /login/ (mô phỏng trình duyệt thật)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('admin', password='admin123')

    def test_login_page_loads(self):
        resp = self.client.get(reverse('accounts:login'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Phụ huynh đăng nhập')

    def test_login_success_redirects_home(self):
        """POST đúng tên/mật khẩu → đăng nhập được, về trang chủ bé."""
        resp = self.client.post(reverse('accounts:login'),
                                {'username': 'admin', 'password': 'admin123'})
        self.assertRedirects(resp, reverse('accounts:home'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_wrong_password_shows_error(self):
        resp = self.client.post(reverse('accounts:login'),
                                {'username': 'admin', 'password': 'sai-mat-khau'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Tên đăng nhập hoặc mật khẩu chưa đúng')

    def test_login_fails_with_csrf_enforced(self):
        """Mô phỏng ĐÚNG trình duyệt: bật kiểm tra CSRF; vẫn phải đăng nhập được."""
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        get = c.get(reverse('accounts:login'))
        token = get.cookies['csrftoken'].value
        resp = c.post(reverse('accounts:login'),
                      {'username': 'admin', 'password': 'admin123', 'csrfmiddlewaretoken': token})
        self.assertRedirects(resp, reverse('accounts:home'))


class ProgressViewTests(ManageTestMixin, TestCase):
    """Tiến độ của bé (khu quản lý): cần mở khoá, lọc owner, gộp số liệu."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')
        cls.other = User.objects.create_user('other', password='pass12345')
        cls.child = ChildProfile.objects.create(owner=cls.parent, name='Bi')
        cls.other_child = ChildProfile.objects.create(owner=cls.other, name='Bo')
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        cls.word = Word.objects.create(topic=cls.topic, text_en='cat', text_vi='con mèo')
        cls.game, _ = GameType.objects.get_or_create(
            code='listen-pick', defaults={'name_vi': 'Nghe chọn', 'module': 'listen_pick'})
        GameResult.objects.create(child=cls.child, game_type=cls.game, topic=cls.topic,
                                  stars=3, score=4, total=4)
        Attempt.objects.create(child=cls.child, word=cls.word, recording='recordings/x.wav')
        GameResult.objects.create(child=cls.other_child, game_type=cls.game, stars=1, score=1, total=4)

    def test_progress_requires_unlock(self):
        self.login()
        self.set_passcode()
        resp = self.client.get(reverse('accounts:progress'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:manage_unlock'), resp.url)

    def test_progress_aggregates_own_children(self):
        self.unlock_manage()
        resp = self.client.get(reverse('accounts:progress'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['total_games'], 1)
        self.assertEqual(resp.context['total_stars'], 3)
        self.assertEqual(resp.context['total_attempts'], 1)

    def test_progress_filter_by_child_owner_enforced(self):
        self.unlock_manage()
        resp = self.client.get(reverse('accounts:progress'), {'child': self.other_child.pk})
        self.assertEqual(resp.status_code, 404)
