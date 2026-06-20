"""
View khu học từ vựng (cho bé xem & nghe).

GĐ 1: danh sách chủ đề → danh sách từ trong chủ đề (có nút 🔊 nghe phát âm).
Đây là nội dung học dùng chung, không lọc theo owner. Yêu cầu đăng nhập
(phụ huynh mở cho bé) để thống nhất với khu còn lại ở GĐ 0.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from . import audio as audio_service
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
