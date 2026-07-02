"""
View khu học từ vựng (cho bé xem & nghe).

GĐ 1: danh sách chủ đề → danh sách từ trong chủ đề (có nút 🔊 nghe phát âm).
Đây là nội dung học dùng chung, không lọc theo owner. Yêu cầu đăng nhập
(phụ huynh mở cho bé) để thống nhất với khu còn lại ở GĐ 0.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from core.decorators import manage_required

from . import audio as audio_service
from . import imports as import_service
from . import ipa as ipa_service
from .forms import TopicForm, WordForm, WordImportForm
from .models import Topic, Word

logger = logging.getLogger('eng.catalog')


@login_required
def topic_list(request):
    """Danh sách chủ đề đang dùng."""
    topics = Topic.objects.filter(active='Y')
    return render(request, 'catalog/topic_list.html', {'topics': topics})


@login_required
def word_list(request, slug):
    """Danh sách từ trong một chủ đề."""
    topic = get_object_or_404(Topic, slug=slug, active='Y')
    words = topic.words.filter(active='Y')
    return render(request, 'catalog/word_list.html', {'topic': topic, 'words': words})


@login_required
def word_audio(request, pk):
    """
    Trả URL audio phát âm của một từ (sinh + cache nếu chưa có).
    Template gọi qua HTMX/JS rồi phát bằng thẻ <audio>. Trả JSON.
    """
    word = get_object_or_404(Word, pk=pk, active='Y')
    clip = audio_service.get_clip(word)
    if not clip:
        # Không sinh được (vd offline và pyttsx3 lỗi) → báo nhẹ nhàng, không 500.
        return JsonResponse({'ok': False, 'message': 'Chưa nghe được, thử lại sau nhé.'}, status=503)
    return JsonResponse({'ok': True, 'url': clip.file.url})


# =====================================================================
# KHU QUẢN LÝ (phụ huynh): CRUD chủ đề / từ vựng + nhập CSV.
# Nội dung học là kho dùng chung (không lọc owner) — cần đăng nhập + passcode.
# =====================================================================

@manage_required
def topic_manage(request):
    """Danh sách chủ đề để quản lý (kèm số từ mỗi chủ đề)."""
    topics = Topic.objects.annotate(num_words=Count('words')).order_by('order', 'name_en')
    return render(request, 'catalog/manage/topic_list.html', {'topics': topics})


@manage_required
def topic_form(request, pk=None):
    """Tạo (pk=None) hoặc sửa chủ đề. slug tự sinh từ name_en nếu để trống."""
    topic = get_object_or_404(Topic, pk=pk) if pk else None
    form = TopicForm(request.POST or None, instance=topic)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        if not obj.slug:  # tự sinh slug khi để trống
            obj.slug = slugify(obj.name_en) or 'topic'
        obj.save()
        messages.success(request, f'Đã lưu chủ đề "{obj.name_vi}".')
        return redirect('catalog_manage:topic_manage')
    return render(request, 'catalog/manage/topic_form.html', {'form': form, 'is_add': topic is None})


@manage_required
def word_manage(request):
    """
    Danh sách từ vựng để quản lý — có lọc theo chủ đề (?topic=<slug>),
    tìm theo từ (?q=), và phân trang.
    """
    words = Word.objects.select_related('topic').order_by('topic__order', 'text_en')
    topic_slug = request.GET.get('topic', '').strip()
    if topic_slug:
        words = words.filter(topic__slug=topic_slug)
    query = request.GET.get('q', '').strip()
    if query:
        # __icontains: nhất quán hoa-thường SQLite↔MySQL (skill §3).
        words = words.filter(text_en__icontains=query)

    paginator = Paginator(words, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'page_obj': page_obj,
        'topics': Topic.objects.all().order_by('order', 'name_en'),
        'topic_slug': topic_slug,
        'query': query,
    }
    return render(request, 'catalog/manage/word_list.html', context)


@manage_required
def word_form(request, pk=None):
    """Tạo/sửa từ vựng. IPA tự sinh khi phonetic để trống (eng-to-ipa)."""
    word = get_object_or_404(Word, pk=pk) if pk else None
    form = WordForm(request.POST or None, request.FILES or None, instance=word)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        if not obj.phonetic:  # tự sinh IPA khi để trống
            obj.phonetic = ipa_service.to_ipa(obj.text_en)
        obj.save()
        messages.success(request, f'Đã lưu từ "{obj.text_en}".')
        return redirect('catalog_manage:word_manage')
    return render(request, 'catalog/manage/word_form.html', {'form': form, 'is_add': word is None})


@manage_required
def word_export(request):
    """
    Xuất TẤT CẢ từ vựng ra file CSV để tải về (backup) — nạp lại được qua màn Nhập CSV.

    Tải toàn bộ (không theo bộ lọc) để restore đầy đủ. Trả file đính kèm (download).
    """
    csv_text = import_service.export_words()
    resp = HttpResponse(csv_text, content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="words_backup.csv"'
    logger.info('Xuất CSV từ vựng (%s từ).', Word.objects.count())
    return resp


@manage_required
def word_import(request):
    """Nhập từ hàng loạt từ file CSV (dùng chung service catalog.imports)."""
    form = WordImportForm(request.POST or None, request.FILES or None)
    stats = None
    if request.method == 'POST' and form.is_valid():
        make_audio = form.cleaned_data['make_audio']
        try:
            stats = import_service.import_csv_file(
                form.cleaned_data['csv_file'], make_audio=make_audio)
        except import_service.ImportError_ as e:
            messages.error(request, str(e))
        else:
            messages.success(
                request,
                f"Nhập xong: {stats['created_topics']} chủ đề mới, "
                f"{stats['created_words']} từ mới, {stats['updated_words']} từ cập nhật.")
            return redirect('catalog_manage:word_manage')
    return render(request, 'catalog/manage/word_import.html', {'form': form, 'stats': stats})
