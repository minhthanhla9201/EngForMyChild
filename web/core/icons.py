"""
Tiện ích icon dùng chung: quy đổi emoji → tên file SVG offline (theo codepoint)
và phân giải đường dẫn tới SVG đã tải trong media/images/.

VÌ SAO: emoji nhúng thô render bằng font hệ thống → deploy sang máy thiếu font
(Windows Server / Linux) sẽ lỗi/không hiện. Giải pháp thống nhất toàn dự án là
render bằng <img> trỏ SVG offline (giống Word.image), không phụ thuộc font.

- fetch_images (tải SVG từ vựng) import emoji_to_filename từ đây — MỘT nguồn sự thật.
- Linh vật (PetStage) / huy hiệu (Badge) dùng emoji_svg_path để fallback khi
  không có ảnh upload riêng.
"""

from django.conf import settings


def emoji_to_filename(emoji):
    """
    Đổi emoji → tên codepoint: nối bằng '-', HOA, bỏ VS16 (FE0F).

    VD '🐱' → '1F431'; '☂️' (U+2602 U+FE0F) → '2602'. (Cả Twemoji lẫn OpenMoji
    đều bỏ FE0F trong tên file cho các emoji thường dùng ở bộ này.)
    """
    cps = [f'{ord(ch):X}' for ch in emoji if ord(ch) != 0xFE0F]
    return '-'.join(cps)


def emoji_svg_path(emoji):
    """
    Trả đường dẫn TƯƠNG ĐỐI (vd 'images/1F431.svg') tới SVG offline của emoji nếu
    file đã tồn tại trong MEDIA_ROOT/images/; ngược lại trả None.

    Chỉ dùng bộ Twemoji ở thư mục gốc images/ (giữ tương thích cơ chế fetch_images).
    Không tải mạng ở đây — chỉ kiểm tra file có sẵn để render offline.
    """
    if not emoji:
        return None
    fname = emoji_to_filename(emoji)
    if not fname:
        return None
    abs_path = settings.MEDIA_ROOT / 'images' / f'{fname}.svg'
    if abs_path.exists():
        return f'images/{fname}.svg'
    return None
