"""
View khu tài khoản (phụ huynh) + trang chủ khu của bé + luồng passcode khu quản lý.

- Trang chủ khu của bé (`/`): chỉ cần đăng nhập, dùng layout base_kid.
- Khu quản lý (`/manage/...`): dùng @manage_required (đăng nhập + passcode), layout base_manage.
- Đăng nhập/đăng xuất dùng view sẵn của Django (khai trong urls.py).
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render

from catalog.models import Topic, Word
from core.decorators import (clear_manage_unlock, manage_required,
                             mark_manage_unlocked)
from games.models import GameResult
from pronunciation.models import Attempt

from .forms import (ChangePasscodeForm, ChildProfileForm, ManageUnlockForm,
                    SetPasscodeForm)
from .models import ChildProfile, ManagePasscode

logger = logging.getLogger('eng.auth')


class ParentLoginView(LoginView):
    """Đăng nhập phụ huynh: ghi log lý do form lỗi để dễ chẩn đoán khi đăng nhập thất bại."""

    template_name = 'accounts/login.html'
    redirect_authenticated_user = True  # đã đăng nhập rồi vào /login/ thì về thẳng trang chủ

    def form_invalid(self, form):
        # Ghi rõ lỗi form (sai mật khẩu / tài khoản khoá...) ra log để soi nguyên nhân thật.
        logger.warning('Đăng nhập thất bại cho username=%r. Lỗi form: %s',
                       form.data.get('username'), form.errors.as_json())
        return super().form_invalid(form)


# =====================================================================
# KHU CỦA BÉ — trang chủ (chỉ cần đăng nhập). Layout base_kid.
# =====================================================================

@login_required
def home(request):
    """Trang chủ khu của bé: 3 hoạt động lớn (Học / Luyện phát âm / Trò chơi)."""
    return render(request, 'accounts/kid_home.html')


# =====================================================================
# VÀO KHU QUẢN LÝ — nhập / đặt passcode (đăng nhập rồi, chưa mở khoá).
# =====================================================================

@login_required
def manage_unlock(request):
    """
    Mở khoá khu quản lý bằng passcode.

    - Chưa đặt passcode (DB) → chuyển sang form ĐẶT passcode lần đầu.
    - Đã đặt → form NHẬP passcode; đúng → mở khoá (lưu thời điểm vào session) → next.
    """
    passcode = ManagePasscode.get_solo()
    next_url = request.GET.get('next') or request.POST.get('next') or 'accounts:dashboard'

    # Lần đầu chưa có passcode → buộc đặt trước.
    if not passcode.is_set:
        form = SetPasscodeForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            passcode.set_passcode(form.cleaned_data['passcode1'])
            mark_manage_unlocked(request)
            messages.success(request, 'Đã đặt passcode khu quản lý.')
            return redirect(next_url)
        return render(request, 'accounts/manage_set_passcode.html',
                      {'form': form, 'next': next_url})

    # Đã có passcode → nhập để mở khoá.
    form = ManageUnlockForm(request.POST or None, passcode_obj=passcode)
    if request.method == 'POST' and form.is_valid():
        mark_manage_unlocked(request)
        return redirect(next_url)
    return render(request, 'accounts/manage_unlock.html', {'form': form, 'next': next_url})


@manage_required
def manage_passcode_change(request):
    """Đổi passcode (trong khu quản lý): phải nhập đúng passcode hiện tại."""
    passcode = ManagePasscode.get_solo()
    form = ChangePasscodeForm(request.POST or None, passcode_obj=passcode)
    if request.method == 'POST' and form.is_valid():
        passcode.set_passcode(form.cleaned_data['passcode1'])
        messages.success(request, 'Đã đổi passcode khu quản lý.')
        return redirect('accounts:dashboard')
    return render(request, 'accounts/manage_change_passcode.html', {'form': form})


def manage_lock(request):
    """Khoá lại khu quản lý (về khu của bé). Không cần passcode để gọi."""
    clear_manage_unlock(request)
    return redirect('accounts:home')


# =====================================================================
# KHU QUẢN LÝ — bảng điều khiển + CRUD hồ sơ bé + tiến độ. @manage_required.
# =====================================================================

@manage_required
def dashboard(request):
    """Bảng điều khiển khu quản lý: số liệu tổng quan + lối tắt + hồ sơ bé."""
    children = ChildProfile.objects.filter(owner=request.user, active='Y')
    stats = {
        'children': children.count(),
        'topics': Topic.objects.filter(active='Y').count(),
        'words': Word.objects.filter(active='Y').count(),
    }
    return render(request, 'accounts/dashboard.html', {'children': children, 'stats': stats})


@manage_required
def progress(request):
    """
    Tiến độ của bé: kết quả chơi (GameResult) + lần luyện phát âm (Attempt).

    Lọc theo owner — chỉ thấy dữ liệu các bé thuộc phụ huynh đang đăng nhập.
    Có thể chọn 1 bé qua ?child=<pk>; mặc định gộp tất cả bé của phụ huynh.
    """
    children = ChildProfile.objects.filter(owner=request.user, active='Y')
    selected = None
    child_pk = request.GET.get('child')
    if child_pk:
        # get_object_or_404 + lọc owner: không xem được tiến độ bé của người khác.
        selected = get_object_or_404(ChildProfile, pk=child_pk, owner=request.user)
        results = GameResult.objects.filter(child=selected)
        attempts = Attempt.objects.filter(child=selected)
    else:
        results = GameResult.objects.filter(child__in=children)
        attempts = Attempt.objects.filter(child__in=children)

    context = {
        'children': children,
        'selected': selected,
        'results': results.select_related('child', 'game_type', 'topic')[:50],
        'attempts': attempts.select_related('child', 'word')[:50],
        'total_stars': sum(r.stars for r in results),
        'total_games': results.count(),
        'total_attempts': attempts.count(),
    }
    return render(request, 'accounts/progress.html', context)


@manage_required
def child_add(request):
    """Tạo hồ sơ bé mới. owner = phụ huynh đang đăng nhập."""
    form = ChildProfileForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        child = form.save(commit=False)
        child.owner = request.user  # luôn gán owner theo người đăng nhập
        child.save()
        messages.success(request, f'Đã thêm bé {child.name}.')
        return redirect('accounts:dashboard')
    return render(request, 'accounts/child_form.html', {'form': form, 'is_add': True})


@manage_required
def child_edit(request, pk):
    """Sửa hồ sơ bé — chỉ hồ sơ thuộc phụ huynh đang đăng nhập (lọc owner → 404 nếu khác)."""
    child = get_object_or_404(ChildProfile, pk=pk, owner=request.user)
    form = ChildProfileForm(request.POST or None, instance=child)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Đã cập nhật bé {child.name}.')
        return redirect('accounts:dashboard')
    return render(request, 'accounts/child_form.html', {'form': form, 'is_add': False})
