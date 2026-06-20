"""
Khuôn game "Nghe & chọn": phát audio một từ, bé chọn đúng từ/hình trong 4 lựa chọn.

Dùng chung kho Word — không có dữ liệu riêng. build_round chọn ngẫu nhiên các câu hỏi,
mỗi câu 1 đáp án đúng + 3 nhiễu (cùng chủ đề nếu đủ).
"""

import random

from .base import stars_from_ratio, word_payload

NUM_CHOICES = 4


def build_round(words, count=5):
    """
    Tạo một vòng chơi gồm tối đa `count` câu hỏi từ danh sách `words` (QuerySet/list).

    Trả dict: {'questions': [{'answer_id', 'audio_word_id', 'choices': [word_payload...]}]}
    audio_word_id để client gọi API audio phát mẫu (qua catalog).
    """
    words = list(words)
    questions = []
    if len(words) < NUM_CHOICES:
        return {'questions': questions}

    # Số câu không vượt quá số từ có.
    n = min(count, len(words))
    targets = random.sample(words, n)
    for target in targets:
        # 3 nhiễu khác target.
        distractor_pool = [w for w in words if w.pk != target.pk]
        distractors = random.sample(distractor_pool, NUM_CHOICES - 1)
        choices = [target] + distractors
        random.shuffle(choices)
        questions.append({
            'answer_id': target.pk,
            'audio_word_id': target.pk,
            'choices': [word_payload(w) for w in choices],
        })
    return {'questions': questions}


def score_round(payload):
    """
    Chấm vòng chơi. payload = {'answers': [{'answer_id', 'picked_id'}, ...]}.
    Trả {'score', 'total', 'stars'}.
    """
    answers = payload.get('answers', []) or []
    total = len(answers)
    score = sum(1 for a in answers if a.get('picked_id') == a.get('answer_id'))
    return {'score': score, 'total': total, 'stars': stars_from_ratio(score, total)}
