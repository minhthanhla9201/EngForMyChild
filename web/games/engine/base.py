"""
Tiện ích dùng chung cho mọi khuôn game.

Mỗi module game expose 2 hàm:
    build_round(words, count) -> dict   # tạo dữ liệu một vòng chơi từ kho Word
    score_round(payload)      -> dict   # chấm: {'score', 'total', 'stars'}

Phần chấm là CHUNG theo KIỂU game — module chỉ gọi lại, không tự viết:
    score_choice_round(payload)  # game trả lời từng câu (nghe/nhìn rồi chọn)
    score_match_round(payload)   # game lật thẻ tìm cặp
"""


def stars_from_ratio(score, total):
    """
    Quy số câu đúng → sao (0–3). Khích lệ, không khắt khe:
      >=90% : 3 sao | >=70% : 2 sao | >=40% : 1 sao | còn lại : 0.
    """
    if total <= 0:
        return 0
    ratio = score / total
    if ratio >= 0.9:
        return 3
    if ratio >= 0.7:
        return 2
    if ratio >= 0.4:
        return 1
    return 0


def word_payload(word):
    """
    Dữ liệu một từ gửi ra client (an toàn, gọn). Hình lấy URL nếu có.

    vi_name_url: audio đọc TÊN tiếng Việt của từ ("con mèo") — bé chưa biết chữ,
    chạm vào hình sẽ nghe tên hình. Gửi sẵn URL để client phát ngay, không round-trip.
    Import trong hàm để tránh vòng import (games → catalog). '' nếu chưa sinh được.
    """
    from catalog.audio import get_vi_name
    return {
        'id': word.pk,
        'text_en': word.text_en,
        'text_vi': word.text_vi,
        'image': word.image.url if word.image else '',
        'vi_name_url': get_vi_name(word) or '',
    }


def score_choice_round(payload):
    """
    Chấm game "trả lời từng câu": mỗi câu `picked_id == answer_id` là đúng.

    payload = {'answers': [{'answer_id', 'picked_id'}, ...]}
    Trả {'score', 'total', 'stars', 'word_results'}.
    """
    answers = payload.get('answers', []) or []
    total = len(answers)
    score = sum(1 for a in answers if a.get('picked_id') == a.get('answer_id'))
    word_results = [
        {'word_id': a['answer_id'], 'correct': a.get('picked_id') == a.get('answer_id')}
        for a in answers if a.get('answer_id')
    ]
    return {'score': score, 'total': total, 'stars': stars_from_ratio(score, total),
            'word_results': word_results}


def score_match_round(payload):
    """
    Chấm game "lật thẻ tìm cặp".

    payload = {'pairs_total', 'pairs_matched', 'mistakes', 'matched_pair_ids', 'pair_ids'}
    Sao tính theo tỉ lệ ghép đúng, trừ nhẹ theo số lần lật sai (mỗi 2 lần sai coi
    như 'mất' 1 điểm hiệu quả) — vẫn khích lệ, không xuống dưới 0.
    word_results: mỗi pair_id chính là word_id.
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
    return {'score': matched, 'total': total,
            'stars': stars_from_ratio(effective, total),
            'word_results': word_results}
