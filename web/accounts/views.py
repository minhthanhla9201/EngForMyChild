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
from progress import service as progress_service

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

# Khoá lưu id bé đang hoạt động ở khu của bé (trong session).
ACTIVE_CHILD_KEY = 'active_child_id'


def get_active_child(request):
    """
    Bé đang hoạt động ở khu của bé (theo session), hoặc None.

    Luôn lọc theo owner để không trả bé của phụ huynh khác. Nếu id trong session
    không hợp lệ (bé đã xoá / đổi tài khoản) thì bỏ qua.
    """
    cid = request.session.get(ACTIVE_CHILD_KEY)
    if not cid:
        return None
    return ChildProfile.objects.filter(pk=cid, owner=request.user, active='Y').first()


@login_required
def home(request):
    """
    Trang chủ khu của bé: chọn bé → hiện tiến độ (sao, linh vật, huy hiệu) +
    3 hoạt động lớn (Học / Luyện phát âm / Trò chơi).

    Nếu chưa chọn bé (và có nhiều bé) → hiện màn chọn bé. Có đúng 1 bé thì tự chọn.
    """
    children = ChildProfile.objects.filter(owner=request.user, active='Y')
    # "Đổi bé": xoá lựa chọn hiện tại để quay lại màn chọn bé.
    if request.GET.get('switch'):
        request.session.pop(ACTIVE_CHILD_KEY, None)
        return redirect('accounts:home')

    active = get_active_child(request)
    # Tự chọn khi chỉ có 1 bé → bé vào thẳng, đỡ một bước bấm.
    if active is None and children.count() == 1:
        active = children.first()
        request.session[ACTIVE_CHILD_KEY] = active.pk

    context = {'children': children, 'active_child': active}
    if active is not None:
        context['progress'] = progress_service.summary(active)
    return render(request, 'accounts/kid_home.html', context)


@login_required
def set_active_child(request, pk):
    """Chọn bé đang hoạt động (lưu session) rồi về trang chủ khu bé."""
    child = get_object_or_404(ChildProfile, pk=pk, owner=request.user, active='Y')
    request.session[ACTIVE_CHILD_KEY] = child.pk
    return redirect('accounts:home')


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


@manage_required
def child_delete(request, pk):
    """
    Xoá hẳn hồ sơ bé + TẤT CẢ dữ liệu liên quan (lần luyện, kết quả chơi).

    Đây là xoá cứng có chủ đích (app local trong gia đình, phụ huynh tự quyết) —
    khác quy ước "xoá mềm" chung, nên phải xác nhận bằng gõ đúng tên bé (chống nhầm).
    Attempt/GameResult có on_delete=CASCADE nên tự xoá theo ở DB; nhưng FILE ghi âm
    trong media/recordings/ Django KHÔNG tự xoá → phải dọn tay TRƯỚC khi xoá bản ghi.
    Chỉ nhận POST (thao tác thay đổi dữ liệu).
    """
    child = get_object_or_404(ChildProfile, pk=pk, owner=request.user)
    if request.method != 'POST':
        return redirect('accounts:child_edit', pk=pk)

    # Xác nhận: phải gõ đúng tên bé (khớp, đã strip khoảng trắng).
    if (request.POST.get('confirm_name') or '').strip() != child.name:
        messages.error(request, 'Tên xác nhận chưa khớp — chưa xoá gì cả.')
        return redirect('accounts:child_edit', pk=pk)

    name = child.name
    # Dọn file ghi âm của bé trước (xoá bản ghi sẽ mất đường dẫn tới file).
    removed_files = 0
    for attempt in child.attempts.all():
        if attempt.recording:
            attempt.recording.delete(save=False)  # xoá file trên đĩa, không đụng DB
            removed_files += 1

    child.delete()  # CASCADE tự xoá Attempt + GameResult của bé
    logger.info('Xoá hồ sơ bé %r (id=%s), dọn %s file ghi âm.', name, pk, removed_files)
    messages.success(request, f'Đã xoá bé {name} cùng toàn bộ dữ liệu liên quan.')
    return redirect('accounts:dashboard')
