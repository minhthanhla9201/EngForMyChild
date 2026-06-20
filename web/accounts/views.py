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
    """Trang chủ phụ huynh: danh sách hồ sơ bé của chính mình."""
    children = ChildProfile.objects.filter(owner=request.user, active='Y')
    return render(request, 'accounts/home.html', {'children': children})


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
