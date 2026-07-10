"""
Template tag hiển thị icon KHÔNG phụ thuộc font hệ thống.

Dùng trong template khu bé/quản lý để render emoji bằng <img> trỏ SVG offline
(giống Word.image), fallback về ký tự emoji nếu không có SVG. VÌ SAO: máy đích
có thể thiếu font emoji → nhúng emoji thô sẽ lỗi.

Cách dùng:
    {% load icons %}
    {% icon_img emoji='🌱' src=stage.icon_src size=64 alt='Linh vật' %}
    {% icon_img emoji='🔒' size=28 %}        {# emoji tĩnh trong HTML #}
"""

from django import template
from django.utils.safestring import mark_safe
from django.templatetags.static import static  # noqa: F401  (dự phòng nếu cần)

from core.icons import emoji_svg_path

register = template.Library()


@register.filter(name='emoji_svg')
def emoji_svg(emoji):
    """Trả URL /media/images/<CP>.svg của emoji nếu có SVG offline, ngược lại ''."""
    rel = emoji_svg_path(emoji)
    if not rel:
        return ''
    from django.conf import settings
    return f'{settings.MEDIA_URL}{rel}'


@register.simple_tag
def icon_img(emoji='', src='', size=40, alt='', css='emoji-svg'):
    """
    Render icon: ưu tiên `src` (ảnh upload hoặc URL SVG sẵn), sau đó SVG offline
    của `emoji`; nếu không có SVG nào thì hiện chính ký tự emoji (fallback text).

    `src` nên là URL đã sẵn (vd model.icon_src trả image.url hoặc /media/... ).
    Thẻ <img> có onerror → thay bằng emoji text nếu ảnh lỗi (an toàn 2 lớp).
    """
    url = src or emoji_svg(emoji)
    px = f'{int(size)}px'
    if url:
        # onerror: nếu ảnh không tải được, thay bằng emoji text để không mất icon.
        safe_alt = alt or 'icon'
        return mark_safe(
            f'<img class="{css}" src="{url}" alt="{safe_alt}" '
            f'style="width:{px};height:{px};object-fit:contain;" '
            f'onerror="this.outerHTML=\'{emoji}\'">'
        )
    # Không có SVG lẫn ảnh → hiện emoji text (kích thước theo size).
    return mark_safe(f'<span class="{css}" style="font-size:{px};line-height:1;">{emoji}</span>')
