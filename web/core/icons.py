"""
Tiện ích icon dùng chung: quy đổi emoji → tên file SVG offline (theo codepoint)
và phân giải đường dẫn tới SVG đã tải trong media/images/.

VÌ SAO: emoji nhúng thô render bằng font hệ thống → deploy sang máy thiếu font
(Windows Server / Linux) sẽ lỗi/không hiện. Giải pháp thống nhất toàn dự án là
render bằng <img> trỏ SVG offline (giống Word.image), không phụ thuộc font.

- fetch_images (tải SVG từ vựng) import emoji_to_filename từ đây — MỘT nguồn sự thật.
- Topic / Badge / PetStage dùng resolve_icon_src để chọn nguồn icon theo thứ tự
  ưu tiên (ảnh upload > SVG tĩnh trong static > SVG offline emoji > fallback text).
"""

from django.conf import settings


def resolve_icon_src(image, icon_static, emoji):
    """
    URL icon để render <img>, theo thứ tự ưu tiên (dùng chung Topic/Badge/PetStage):
    1) ảnh upload (media) — người quản lý tự đặt riêng;
    2) SVG tĩnh trong static (repo) — MẶC ĐỊNH, commit theo mã nguồn nên deploy
       máy khác luôn có, không cần mạng, không phụ thuộc font;
    3) SVG offline của emoji trong media (nếu đã fetch);
    4) '' → template hiển thị ký tự emoji (fallback cuối).

    `image` là FileField/ImageField (hoặc falsy); `icon_static` là đường dẫn static
    (vd 'icons/topic/animals.svg'); `emoji` là ký tự emoji.
    """
    if image:
        return image.url
    if icon_static:
        from django.templatetags.static import static
        return static(icon_static)
    rel = emoji_svg_path(emoji)
    if rel:
        return f'{settings.MEDIA_URL}{rel}'
    return ''


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
