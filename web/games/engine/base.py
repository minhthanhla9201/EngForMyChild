"""
Tiện ích dùng chung cho mọi khuôn game.

Mỗi module game expose 2 hàm:
    build_round(words, count) -> dict   # tạo dữ liệu một vòng chơi từ kho Word
    score_round(payload)      -> dict   # chấm: {'score', 'total', 'stars'}

Phần quy đổi sao là CHUNG (stars_from_ratio) — không lặp ở từng game.
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
