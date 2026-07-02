"""
Khuôn game "Nhìn hình & nghe chọn từ": hiện 1 HÌNH lớn, bé nghe 4 audio (chạm
loa để nghe từng cái) rồi chọn audio đọc đúng tên hình.

Ngược chiều với listen_pick_image (ở đó nghe → chọn hình; ở đây nhìn → chọn
tiếng). Cũng dành cho bé chưa biết chữ: lựa chọn là nút LOA, không phải chữ.
Chỉ dùng từ có ảnh (needs_image='Y').
"""

import random

from .base import stars_from_ratio, word_payload

NUM_CHOICES = 4


def build_round(words, count=5):
    """
    Mỗi câu: 1 hình đáp án + 4 lựa chọn audio (1 đúng, 3 nhiễu).

    Trả {'questions': [{'answer_id', 'image_word_id', 'choices': [word_payload...]}]}.
    image_word_id để client hiện hình; mỗi choice có id để client gọi API audio phát.
    """
    words = list(words)
    questions = []
    if len(words) < NUM_CHOICES:
        return {'questions': questions}

    n = min(count, len(words))
    targets = random.sample(words, n)
    for target in targets:
        # 3 audio nhiễu khác đáp án (cùng kho từ chủ đề).
        distractor_pool = [w for w in words if w.pk != target.pk]
        distractors = random.sample(distractor_pool, NUM_CHOICES - 1)
        choices = [target] + distractors
        random.shuffle(choices)
        questions.append({
            'answer_id': target.pk,
            'image_word_id': target.pk,
            'choices': [word_payload(w) for w in choices],
        })
    return {'questions': questions}


def score_round(payload):
    """Chấm: mỗi câu picked_id (id từ có audio bé chọn) == answer_id là đúng."""
    answers = payload.get('answers', []) or []
    total = len(answers)
    score = sum(1 for a in answers if a.get('picked_id') == a.get('answer_id'))
    return {'score': score, 'total': total, 'stars': stars_from_ratio(score, total)}
