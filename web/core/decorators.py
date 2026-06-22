"""
Tiện ích phân quyền khu quản lý.

manage_required: chặn truy cập khu quản lý — vừa phải đăng nhập, vừa phải đã
"mở khoá" bằng passcode trong vòng MANAGE_UNLOCK_MINUTES phút gần đây (trượt
hạn theo thao tác). Thiếu → chuyển tới màn nhập passcode (kèm ?next để quay lại).
"""

import functools

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

# Khoá lưu thời điểm mở khoá (ISO string) trong session.
SESSION_KEY = 'manage_unlocked_at'


def is_manage_unlocked(request):
    """Phiên hiện tại đã mở khoá khu quản lý và còn hạn chưa?"""
    raw = request.session.get(SESSION_KEY)
    if not raw:
        return False
    ts = timezone.datetime.fromisoformat(raw)
    age = (timezone.now() - ts).total_seconds()
    return age <= settings.MANAGE_UNLOCK_MINUTES * 60


def mark_manage_unlocked(request):
    """Đánh dấu phiên vừa mở khoá (gọi sau khi nhập passcode đúng, và mỗi lần
    qua được manage_required → trượt hạn)."""
    request.session[SESSION_KEY] = timezone.now().isoformat()


def clear_manage_unlock(request):
    """Xoá mở khoá (khi khoá lại / đăng xuất)."""
    request.session.pop(SESSION_KEY, None)


def manage_required(view_func):
    """
    Decorator cho view khu quản lý: yêu cầu đăng nhập + đã mở khoá passcode.

    - Chưa đăng nhập → @login_required lo (redirect /login/).
    - Đã đăng nhập nhưng chưa mở khoá / hết hạn → chuyển tới màn nhập passcode,
      kèm ?next=<đường dẫn hiện tại> để quay lại sau khi mở khoá.
    - Đã mở khoá & còn hạn → cho qua, đồng thời gia hạn (trượt hạn).
    """
    @login_required
    @functools.wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_manage_unlocked(request):
            url = reverse('accounts:manage_unlock')
            return redirect(f'{url}?{urlencode({"next": request.get_full_path()})}')
        # Còn hạn → trượt hạn rồi cho qua.
        mark_manage_unlocked(request)
        return view_func(request, *args, **kwargs)

    return _wrapped
