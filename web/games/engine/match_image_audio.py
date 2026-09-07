"""
Khuôn game "Ghép hình với âm thanh" (memory không-chữ): mỗi từ thành 2 thẻ —
một thẻ HÌNH và một thẻ LOA (chạm để nghe audio). Bé lật để ghép hình đúng với
tiếng đọc của nó.

Bản không-chữ của match_pairs (ở đó ghép chữ Anh↔Việt). Dành cho bé chưa biết
chữ. Chỉ dùng từ có ảnh (needs_image='Y'). Chấm dùng chung stars_from_ratio.
"""

import random

from catalog.audio import get_vi_name
from .base import score_match_round

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
    """Chấm ghép cặp hình–tiếng — luật chung của game lật thẻ (xem base)."""
    return score_match_round(payload)
