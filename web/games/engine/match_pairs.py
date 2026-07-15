"""
Khuôn game "Lật thẻ tìm cặp" (memory): mỗi từ thành 2 thẻ (mặt tiếng Anh & mặt
nghĩa tiếng Việt). Bé lật để ghép cặp đúng.

Dùng chung kho Word. Chấm theo độ chính xác: ít lần lật sai → nhiều sao.
"""

import random

from .base import stars_from_ratio

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
    """
    Chấm. payload = {'pairs_total': int, 'pairs_matched': int, 'mistakes': int,
                     'matched_pair_ids': [int, ...]}.

    Sao tính theo tỉ lệ ghép đúng, trừ nhẹ theo số lần sai (mỗi 2 lần sai coi như
    'mất' 1 điểm hiệu quả) — vẫn khích lệ, tối thiểu giữ số cặp đã ghép.
    word_results: mỗi pair_id = word_id.
    """
    total = int(payload.get('pairs_total', 0) or 0)
    matched = int(payload.get('pairs_matched', 0) or 0)
    mistakes = int(payload.get('mistakes', 0) or 0)
    effective = max(matched - mistakes // 2, 0)

    # word_results từ matched_pair_ids.
    matched_ids = set(payload.get('matched_pair_ids', []) or [])
    pair_ids = set(payload.get('pair_ids', []) or [])
    word_results = [
        {'word_id': pid, 'correct': pid in matched_ids}
        for pid in pair_ids
    ]

    return {
        'score': matched,
        'total': total,
        'stars': stars_from_ratio(effective, total),
        'word_results': word_results,
    }
