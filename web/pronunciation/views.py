"""
View luyện phát âm.

Luồng (GĐ 2):
  1) Chọn bé + chủ đề → vào màn luyện.
  2) Màn luyện hiện 1 từ: bé nghe mẫu (dùng API audio của catalog) rồi bấm thu giọng.
  3) Ghi âm xong → POST lên server → lưu Attempt (chưa chấm điểm) → chuyển từ kế tiếp.

Bé luyện không đăng nhập riêng, nhưng phụ huynh phải đăng nhập và chỉ thao tác
trên hồ sơ bé của mình (kiểm owner) — thống nhất với khu còn lại.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from accounts.models import ChildProfile
from catalog.models import Topic, Word
from catalog import praise as praise_service
from progress import service as progress_service
from . import asr as asr_service
from .models import Attempt

logger = logging.getLogger('eng.pron')


@login_required
def choose(request):
    """Chọn bé + chủ đề để bắt đầu luyện phát âm."""
    children = ChildProfile.objects.filter(owner=request.user, active='Y')
    topics = Topic.objects.filter(active='Y')
    return render(request, 'pronunciation/choose.html', {'children': children, 'topics': topics})


@login_required
def practice(request, child_id, slug):
    """Màn luyện phát âm cho một bé trong một chủ đề."""
    # Chỉ cho luyện trên hồ sơ bé của chính phụ huynh (lọc owner → 404 nếu khác).
    child = get_object_or_404(ChildProfile, pk=child_id, owner=request.user, active='Y')
    topic = get_object_or_404(Topic, slug=slug, active='Y')
    words = topic.words.filter(active='Y')

    # Danh sách từ cho client (Alpine). Truyền list thuần — template dùng json_script
    # để serialize (KHÔNG json.dumps ở đây, tránh mã hoá 2 lần → client nhận chuỗi).
    # Dùng ẢNH THẬT của từ (w.image) như bên games; template fallback icon khi từ chưa có ảnh.
    words_data = [{
        'id': w.pk,
        'text_en': w.text_en,
        'text_vi': w.text_vi,
        'phonetic': w.phonetic,
        'image': w.image.url if w.image else '',
    } for w in words]

    return render(request, 'pronunciation/practice.html', {
        'child': child, 'topic': topic, 'words_data': words_data, 'empty': not words.exists(),
    })


@login_required
def save_attempt(request, child_id, word_id):
    """
    Nhận bản ghi giọng bé (multipart) → lưu Attempt. Trả JSON.
    GĐ 2 chưa chấm điểm; trả 'đã lưu' để giao diện khích lệ bé.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Phương thức không hợp lệ.'}, status=405)

    child = get_object_or_404(ChildProfile, pk=child_id, owner=request.user, active='Y')
    word = get_object_or_404(Word, pk=word_id, active='Y')

    audio = request.FILES.get('audio')
    if not audio:
        return JsonResponse({'ok': False, 'message': 'Chưa nhận được bản ghi.'}, status=400)

    attempt = Attempt.objects.create(child=child, word=word, recording=audio)
    logger.info('Lưu bản ghi luyện: bé=%s từ=%s (attempt=%s)', child.name, word.text_en, attempt.pk)

    # Chấm phát âm qua service ASR (so mức từ). ASR tắt/lỗi → result None: vẫn lưu
    # bản ghi, chỉ không chấm (báo thân thiện) — không chặn bé, không 500.
    result = asr_service.score(attempt.recording, word.text_en)
    scored = result is not None
    if scored:
        attempt.asr_text = result['heard'][:255]
        attempt.score = result['score']
        attempt.stars = result['stars']
        attempt.save(update_fields=['asr_text', 'score', 'stars', 'updated_at', 'updated_by'])
        logger.info('Chấm phát âm: từ=%s nghe=%r điểm=%s sao=%s',
                    word.text_en, result['heard'], result['score'], result['stars'])

    # Trao huy hiệu vừa đủ điều kiện (vd "Tập nói", chuỗi ngày) → hiện cho bé.
    new_badges = progress_service.check_and_award_badges(child)

    # Thông điệp khích lệ theo số sao (bé chưa biết chữ → giọng + sao là chính).
    if not scored:
        message = 'Đã ghi lại rồi nhé! (Chưa chấm được, thử lại sau nha.)'
    elif result['stars'] >= 3:
        message = 'Con đọc giỏi quá!'
    elif result['stars'] == 2:
        message = 'Gần đúng rồi, nghe lại rồi thử lại nhé!'
    elif result['stars'] == 1:
        message = 'Cố lên nào, nghe kỹ rồi đọc lại nhé!'
    else:
        message = 'Mình thử lại nhé, nghe mẫu trước nha!'

    return JsonResponse({
        'ok': True,
        'scored': scored,
        'stars': result['stars'] if scored else None,
        'heard': result['heard'] if scored else '',
        'target': word.text_en,
        'message': message,
        'badges': [{'icon': b.icon, 'name_vi': b.name_vi, 'desc_vi': b.desc_vi,
                    'voice_url': praise_service.badge_voice_url(b.desc_vi)}
                   for b in new_badges],
    })
