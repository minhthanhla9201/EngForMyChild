"""Test khu tài khoản: yêu cầu đăng nhập, lọc owner, happy path, audit tự điền."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from catalog.models import Topic, Word
from games.models import GameResult, GameType
from pronunciation.models import Attempt

from .models import ChildProfile


class ChildProfileViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Hai phụ huynh khác nhau để kiểm tra cách ly dữ liệu theo owner.
        cls.parent = User.objects.create_user('parent', password='pass12345')
        cls.other = User.objects.create_user('other', password='pass12345')
        cls.child = ChildProfile.objects.create(owner=cls.parent, name='Bi')
        cls.other_child = ChildProfile.objects.create(owner=cls.other, name='Bo')

    def test_home_requires_login(self):
        """Chưa đăng nhập → redirect sang trang login."""
        resp = self.client.get(reverse('accounts:home'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), resp.url)

    def test_home_lists_only_own_children(self):
        """Phụ huynh chỉ thấy hồ sơ bé của mình."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('accounts:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Bi')
        self.assertNotContains(resp, 'Bo')

    def test_add_child_sets_owner_and_audit(self):
        """POST tạo bé: owner = người đăng nhập, created_by tự điền qua middleware."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.post(reverse('accounts:child_add'),
                                {'name': 'Na', 'birth_year': 2018, 'avatar': '🐥'})
        self.assertRedirects(resp, reverse('accounts:home'))
        child = ChildProfile.objects.get(name='Na')
        self.assertEqual(child.owner, self.parent)
        self.assertEqual(child.created_by, self.parent)

    def test_cannot_edit_other_parent_child(self):
        """Không sửa được hồ sơ bé của phụ huynh khác → 404."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('accounts:child_edit', args=[self.other_child.pk]))
        self.assertEqual(resp.status_code, 404)


class LoginViewTests(TestCase):
    """Kiểm chứng luồng đăng nhập qua trang /login/ (mô phỏng trình duyệt thật)."""

    @classmethod
    def setUpTestData(cls):
        # Tạo đúng tài khoản như trên máy thật: admin / admin123.
        cls.user = User.objects.create_user('admin', password='admin123')

    def test_login_page_loads(self):
        """GET trang login → 200 và có form."""
        resp = self.client.get(reverse('accounts:login'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Phụ huynh đăng nhập')

    def test_login_success_redirects_home(self):
        """POST đúng tên/mật khẩu → đăng nhập được và chuyển về trang chủ.

        Django test client tự xử lý CSRF (enforce_csrf_checks=False mặc định),
        nên test này tách bạch: lỗi (nếu có) là ở form/credential, KHÔNG phải CSRF.
        """
        resp = self.client.post(reverse('accounts:login'),
                                {'username': 'admin', 'password': 'admin123'})
        self.assertRedirects(resp, reverse('accounts:home'))
        # Phiên đã đăng nhập thật sự.
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_wrong_password_shows_error(self):
        """POST sai mật khẩu → ở lại trang login (200) và hiện thông báo lỗi."""
        resp = self.client.post(reverse('accounts:login'),
                                {'username': 'admin', 'password': 'sai-mat-khau'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Tên đăng nhập hoặc mật khẩu chưa đúng')

    def test_login_fails_with_csrf_enforced(self):
        """
        Mô phỏng ĐÚNG trình duyệt: bật kiểm tra CSRF.
        GET để lấy cookie+token CSRF, rồi POST kèm token → vẫn phải đăng nhập được.
        Nếu test này rớt mà test trên đậu => vấn đề nằm ở CSRF (cookie/Origin), không phải mật khẩu.
        """
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        get = c.get(reverse('accounts:login'))
        token = get.cookies['csrftoken'].value
        resp = c.post(reverse('accounts:login'),
                      {'username': 'admin', 'password': 'admin123', 'csrfmiddlewaretoken': token})
        self.assertRedirects(resp, reverse('accounts:home'))


class DashboardTests(TestCase):
    """Test bảng điều khiển: hiển thị 2 khu + số liệu tổng quan."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')
        cls.child = ChildProfile.objects.create(owner=cls.parent, name='Bi')
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        Word.objects.create(topic=cls.topic, text_en='cat', text_vi='con mèo')

    def test_dashboard_shows_zones_and_stats(self):
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('accounts:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Khu của bé')
        self.assertContains(resp, 'Khu quản lý')
        # Số liệu: 1 bé, 1 chủ đề, 1 từ.
        self.assertEqual(resp.context['stats'], {'children': 1, 'topics': 1, 'words': 1})


class ProgressViewTests(TestCase):
    """Test tiến độ của bé: yêu cầu đăng nhập, lọc owner, gộp số liệu."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = User.objects.create_user('parent', password='pass12345')
        cls.other = User.objects.create_user('other', password='pass12345')
        cls.child = ChildProfile.objects.create(owner=cls.parent, name='Bi')
        cls.other_child = ChildProfile.objects.create(owner=cls.other, name='Bo')
        cls.topic = Topic.objects.create(name_en='Animals', name_vi='Động vật', slug='animals')
        cls.word = Word.objects.create(topic=cls.topic, text_en='cat', text_vi='con mèo')
        # get_or_create: 'listen-pick' có thể đã được data migration của games gieo sẵn.
        cls.game, _ = GameType.objects.get_or_create(
            code='listen-pick', defaults={'name_vi': 'Nghe chọn', 'module': 'listen_pick'})
        GameResult.objects.create(child=cls.child, game_type=cls.game, topic=cls.topic,
                                  stars=3, score=4, total=4)
        Attempt.objects.create(child=cls.child, word=cls.word, recording='recordings/x.wav')
        # Dữ liệu của bé người khác — không được lọt vào tiến độ của parent.
        GameResult.objects.create(child=cls.other_child, game_type=cls.game, stars=1, score=1, total=4)

    def test_progress_requires_login(self):
        resp = self.client.get(reverse('accounts:progress'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), resp.url)

    def test_progress_aggregates_own_children(self):
        """Mặc định gộp tất cả bé của phụ huynh; không tính bé người khác."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('accounts:progress'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['total_games'], 1)      # chỉ ván của Bi
        self.assertEqual(resp.context['total_stars'], 3)
        self.assertEqual(resp.context['total_attempts'], 1)

    def test_progress_filter_by_child_owner_enforced(self):
        """?child=<bé người khác> → 404 (lọc owner)."""
        self.client.login(username='parent', password='pass12345')
        resp = self.client.get(reverse('accounts:progress'), {'child': self.other_child.pk})
        self.assertEqual(resp.status_code, 404)
