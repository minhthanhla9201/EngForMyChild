"""
Tiện ích dùng chung cho accounts app — tách khỏi views.py để các app khác
(catalog, games, pronunciation) import mà không gây circular import.
"""

# Khoá lưu id bé đang hoạt động ở khu của bé (trong session).
ACTIVE_CHILD_KEY = 'active_child_id'


def get_active_child(request):
    """
    Bé đang hoạt động ở khu của bé (theo session), hoặc None.

    Luôn lọc theo owner để không trả bé của phụ huynh khác. Nếu id trong session
    không hợp lệ (bé đã xoá / đổi tài khoản) thì bỏ qua.
    """
    cid = request.session.get(ACTIVE_CHILD_KEY)
    if not cid:
        return None
    from .models import ChildProfile
    return ChildProfile.objects.filter(pk=cid, owner=request.user, active='Y').first()
