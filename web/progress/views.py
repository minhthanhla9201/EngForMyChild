"""
Khu quản lý (phụ huynh): CRUD linh vật (PetStage) & huy hiệu (Badge).

Đây là kho dùng chung cho mọi bé (không lọc owner) — cần đăng nhập + passcode
(@manage_required), giống khu quản lý nội dung ở catalog. Cho phép phụ huynh tự
đổi icon (upload ảnh hoặc emoji → SVG offline) để không phụ thuộc font máy đích.
"""

import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from core.decorators import manage_required
from .forms import BadgeForm, PetStageForm
from .models import Badge, PetStage

logger = logging.getLogger('eng.progress')


@manage_required
def petstage_manage(request):
    """Danh sách mốc linh vật (theo ngưỡng sao tăng dần)."""
    stages = PetStage.objects.all().order_by('threshold')
    return render(request, 'progress/manage/petstage_list.html', {'stages': stages})


@manage_required
def petstage_form(request, pk=None):
    """Tạo (pk=None) hoặc sửa một mốc linh vật."""
    stage = get_object_or_404(PetStage, pk=pk) if pk else None
    form = PetStageForm(request.POST or None, request.FILES or None, instance=stage)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        messages.success(request, f'Đã lưu mốc linh vật "{obj.name_vi}".')
        return redirect('progress_manage:petstage_manage')
    return render(request, 'progress/manage/petstage_form.html',
                  {'form': form, 'is_add': stage is None, 'stage': stage})


@manage_required
def badge_manage(request):
    """Danh sách huy hiệu để quản lý."""
    badges = Badge.objects.all().order_by('order', 'threshold')
    return render(request, 'progress/manage/badge_list.html', {'badges': badges})


@manage_required
def badge_form(request, pk=None):
    """Tạo/sửa một huy hiệu."""
    badge = get_object_or_404(Badge, pk=pk) if pk else None
    form = BadgeForm(request.POST or None, request.FILES or None, instance=badge)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        messages.success(request, f'Đã lưu huy hiệu "{obj.name_vi}".')
        return redirect('progress_manage:badge_manage')
    return render(request, 'progress/manage/badge_form.html',
                  {'form': form, 'is_add': badge is None, 'badge': badge})
