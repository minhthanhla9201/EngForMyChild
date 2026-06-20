"""
View khu tài khoản (phụ huynh).

GĐ 0: trang chủ + CRUD hồ sơ bé (lọc theo owner). Đăng nhập/đăng xuất dùng
view sẵn của Django (khai trong urls.py).
"""

import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from catalog.models import Topic, Word
from games.models import GameResult
from pronunciation.models import Attempt

from .forms import ChildProfileForm
from .models import ChildProfile

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


@login_required
def home(request):
    """
    Bảng điều khiển phụ huynh.

    Tách rõ 2 khu: "Khu của bé" (vào học/chơi/phát âm) và "Khu quản lý"
    (hồ sơ bé, từ vựng, tiến độ). Kèm vài con số tổng quan để dễ nắm tình hình.
    """
    children = ChildProfile.objects.filter(owner=request.user, active='Y')
    # Số liệu tổng quan cho dashboard (nội dung học là kho chung, không lọc owner).
    stats = {
        'children': children.count(),
        'topics': Topic.objects.filter(active='Y').count(),
        'words': Word.objects.filter(active='Y').count(),
    }
    return render(request, 'accounts/home.html', {'children': children, 'stats': stats})


@login_required
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


@login_required
def child_add(request):
    """Tạo hồ sơ bé mới. owner = phụ huynh đang đăng nhập."""
    form = ChildProfileForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        child = form.save(commit=False)
        child.owner = request.user  # luôn gán owner theo người đăng nhập
        child.save()
        messages.success(request, f'Đã thêm bé {child.name}.')
        return redirect('accounts:home')
    return render(request, 'accounts/child_form.html', {'form': form, 'is_add': True})


@login_required
def child_edit(request, pk):
    """Sửa hồ sơ bé — chỉ hồ sơ thuộc phụ huynh đang đăng nhập (lọc owner → 404 nếu khác)."""
    child = get_object_or_404(ChildProfile, pk=pk, owner=request.user)
    form = ChildProfileForm(request.POST or None, instance=child)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Đã cập nhật bé {child.name}.')
        return redirect('accounts:home')
    return render(request, 'accounts/child_form.html', {'form': form, 'is_add': False})
