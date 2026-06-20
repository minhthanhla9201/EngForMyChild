"""
Middleware lưu user của request hiện tại vào thread-local.

Mục đích: cho AuditedModel.save() tự điền created_by/updated_by mà không phải
truyền user qua từng view (giữ view mỏng). Mỗi request một thread → an toàn.
"""

import threading

# Nơi lưu user theo từng thread xử lý request.
_thread_locals = threading.local()


def get_current_user():
    """Trả về user đang đăng nhập của request hiện tại, hoặc None nếu không có."""
    return getattr(_thread_locals, 'user', None)


class CurrentUserMiddleware:
    """Gán request.user vào thread-local trước khi view chạy, dọn sau khi xong."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Chỉ lưu user đã xác thực; bé chơi không đăng nhập → để None (created_by null).
        user = getattr(request, 'user', None)
        _thread_locals.user = user if (user and user.is_authenticated) else None
        try:
            return self.get_response(request)
        finally:
            # Tránh rò rỉ user sang request khác dùng lại cùng thread.
            _thread_locals.user = None
