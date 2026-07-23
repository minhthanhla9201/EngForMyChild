"""
Template tag phân trang thông minh: hiển thị tối đa 5 button số trang + mũi tên.

Cách dùng trong template:
{% load pagination %}
{% render_pagination results_page "page_r" %}
"""
from urllib.parse import urlencode

from django import template

register = template.Library()


def _build_page_range(current: int, total: int, max_buttons: int = 5) -> list:
    """
    Trả về list các giá trị để render pagination.
    - Giá trị int = số trang
    - Giá trị None = dấu ...
    Luôn giữ tối đa `max_buttons` button số trang.
    """
    if total <= max_buttons:
        return list(range(1, total + 1))

    remaining = max_buttons - 2  # Số slot còn lại sau khi trừ trang đầu và cuối
    half = remaining // 2

    # Cửa sổ trang quanh trang hiện tại
    win_start = max(2, current - half)
    win_end = min(total - 1, current + half)

    # Mở rộng cửa sổ khi ở gần mép
    if win_start <= 2:
        win_end = min(total - 1, 1 + remaining)
    elif win_end >= total - 1:
        win_start = max(2, total - remaining)

    pages = [1]  # Luôn hiện trang đầu

    if win_start > 2:
        pages.append(None)  # ...

    for i in range(win_start, win_end + 1):
        pages.append(i)

    if win_end < total - 1:
        pages.append(None)  # ...

    if total > 1:
        pages.append(total)  # Luôn hiện trang cuối

    return pages


@register.inclusion_tag('pagination.html', takes_context=True)
def render_pagination(context, page_obj, param_name):
    """
    Render thanh phân trang.

    page_obj: Django Page object (có .number, .paginator, .has_previous(), ...)
    param_name: tên query param, vd 'page_r' hoặc 'page_a'
    """
    request = context['request']
    total = page_obj.paginator.num_pages
    page_range = _build_page_range(page_obj.number, total)

    # Xây base params từ request.GET (dùng dict thường, tránh QueryDict copy bug)
    base_params = {}
    for key in request.GET:
        if key != param_name:
            base_params[key] = request.GET[key]

    def _url(page):
        """Tạo URL với page cụ thể, giữ nguyên các param khác."""
        params = dict(base_params)
        params[param_name] = str(page)
        return '?' + urlencode(params)

    # Build URL cho từng nút
    items = []
    for p in page_range:
        items.append({
            'page': p,
            'url': _url(p) if p is not None else None,
            'is_active': p == page_obj.number,
        })

    return {
        'page_obj': page_obj,
        'items': items,
        'has_prev': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'first_url': _url(1) if page_obj.has_previous() else None,
        'prev_url': _url(page_obj.previous_page_number()) if page_obj.has_previous() else None,
        'next_url': _url(page_obj.next_page_number()) if page_obj.has_next() else None,
        'last_url': _url(total) if page_obj.has_next() else None,
    }
