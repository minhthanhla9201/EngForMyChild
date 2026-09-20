"""
Khuôn game "Lật thẻ tìm cặp" (memory): mỗi từ thành 2 thẻ (mặt tiếng Anh & mặt
nghĩa tiếng Việt). Bé lật để ghép cặp đúng.

Dùng chung kho Word. Chấm theo độ chính xác: ít lần lật sai → nhiều sao.
"""

import random

from .base import score_match_round

DEFAULT_PAIRS = 6


def build_round(words, count=DEFAULT_PAIRS):
    """
    Tạo bộ thẻ từ `count` cặp. Trả {'pairs': [...], 'cards': [shuffled cards]}.
    Mỗi card: {'pair_id', 'face': 'en'|'vi', 'text'}.
    """
    words = list(words)
    n = min(count, len(words))
    if n < 2:
        return {'pairs': [], 'cards': []}

    chosen = random.sample(words, n)
    cards = []
    pairs = []
    for w in chosen:
        pairs.append({'pair_id': w.pk, 'en': w.text_en, 'vi': w.text_vi})
        cards.append({'pair_id': w.pk, 'face': 'en', 'text': w.text_en})
        cards.append({'pair_id': w.pk, 'face': 'vi', 'text': w.text_vi})
    random.shuffle(cards)
    return {'pairs': pairs, 'cards': cards}


def score_round(payload):
    """Chấm ghép cặp — luật chung của game lật thẻ (xem base)."""
    return score_match_round(payload)
