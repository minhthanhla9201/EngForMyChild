"""
Khuôn game "Ghép hình với âm thanh" (memory không-chữ): mỗi từ thành 2 thẻ —
một thẻ HÌNH và một thẻ LOA (chạm để nghe audio). Bé lật để ghép hình đúng với
tiếng đọc của nó.

Bản không-chữ của match_pairs (ở đó ghép chữ Anh↔Việt). Dành cho bé chưa biết
chữ. Chỉ dùng từ có ảnh (needs_image='Y'). Chấm dùng chung stars_from_ratio.
"""

import random

from catalog.audio import get_vi_name
from .base import stars_from_ratio

DEFAULT_PAIRS = 6


def build_round(words, count=DEFAULT_PAIRS):
    """
    Tạo bộ thẻ từ `count` cặp. Trả {'pairs': [...], 'cards': [shuffled cards]}.

    Mỗi card: {'pair_id', 'face': 'image'|'audio', 'image', 'word_id'}.
    - face 'image': client hiện ảnh (image).
    - face 'audio': client hiện nút loa, chạm để phát audio (gọi API theo word_id).
    """
    words = list(words)
    n = min(count, len(words))
    if n < 2:
        return {'pairs': [], 'cards': []}

    chosen = random.sample(words, n)
    cards = []
    pairs = []
    for w in chosen:
        image_url = w.image.url if w.image else ''
        # vi_name_url: đọc tên tiếng Việt của hình khi bé lật thẻ HÌNH (chưa biết chữ).
        vi_name_url = get_vi_name(w) or ''
        pairs.append({'pair_id': w.pk, 'image': image_url, 'word_id': w.pk})
        cards.append({'pair_id': w.pk, 'face': 'image', 'image': image_url,
                      'word_id': w.pk, 'vi_name_url': vi_name_url})
        cards.append({'pair_id': w.pk, 'face': 'audio', 'image': '', 'word_id': w.pk})
    random.shuffle(cards)
    return {'pairs': pairs, 'cards': cards}


def score_round(payload):
    """
    Chấm giống match_pairs: payload = {'pairs_total', 'pairs_matched', 'mistakes',
                                        'matched_pair_ids': [int, ...]}.
    Sao theo tỉ lệ ghép đúng, trừ nhẹ theo số lần lật sai (khích lệ, không âm).
    word_results: mỗi pair_id = word_id.
    """
    total = int(payload.get('pairs_total', 0) or 0)
    matched = int(payload.get('pairs_matched', 0) or 0)
    mistakes = int(payload.get('mistakes', 0) or 0)
    effective = max(matched - mistakes // 2, 0)

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
