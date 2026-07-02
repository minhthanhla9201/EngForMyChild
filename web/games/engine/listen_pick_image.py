"""
Khuôn game "Nghe & chọn hình": phát audio một từ, bé chọn đúng HÌNH trong 4 lựa chọn.

Dành cho bé CHƯA BIẾT CHỮ — đáp án là hình ảnh, không phải chữ. Chỉ dùng từ có
ảnh (GameType.needs_image='Y'). Luật/chấm điểm giống listen_pick, chỉ khác cách
hiển thị ở template (hình thay vì chữ) nên tái dùng chung logic.
"""

from .base import stars_from_ratio, word_payload

NUM_CHOICES = 4


def build_round(words, count=5):
    """
    Tạo vòng chơi: mỗi câu phát audio 1 từ, bé chọn hình đúng trong 4 hình.

    Trả {'questions': [{'answer_id', 'audio_word_id', 'choices': [word_payload...]}]}.
    Dùng chung định dạng với listen_pick để template/chấm nhất quán; điểm khác là
    template render `image` của mỗi choice thay vì chữ.
    """
    # Tái dùng nguyên logic của listen_pick (cùng cấu trúc câu hỏi/nhiễu).
    from . import listen_pick
    return listen_pick.build_round(words, count=count)


def score_round(payload):
    """Chấm giống nghe & chọn: mỗi câu picked_id == answer_id là đúng."""
    answers = payload.get('answers', []) or []
    total = len(answers)
    score = sum(1 for a in answers if a.get('picked_id') == a.get('answer_id'))
    return {'score': score, 'total': total, 'stars': stars_from_ratio(score, total)}
