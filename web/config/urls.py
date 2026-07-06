"""URL gốc dự án EngForMyChild."""

import re

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    # --- KHU CỦA BÉ (chỉ cần đăng nhập) ---
    path('learn/', include('catalog.urls')),       # học từ vựng
    path('speak/', include('pronunciation.urls')),  # luyện phát âm
    path('games/', include('games.urls')),          # trò chơi
    # --- KHU QUẢN LÝ NỘI DUNG (cần đăng nhập + passcode) ---
    path('manage/', include('catalog.urls_manage')),
    # Khu tài khoản: trang chủ bé, đăng nhập, và /manage/ (dashboard, hồ sơ bé, tiến độ, passcode).
    path('', include('accounts.urls')),
]

# Phục vụ file media (audio/ảnh/ghi âm). Media sinh runtime (TTS, ghi âm của bé) nên
# KHÔNG dùng WhiteNoise (chỉ quét 1 lần lúc start). serve đọc đĩa mỗi request → thấy file mới.
# Đăng ký trực tiếp bằng re_path (KHÔNG dùng helper static() vì nó tự no-op khi DEBUG=False),
# để media hoạt động cả khi DEBUG=False — app chạy local, không có web server ngoài serve /media.
# Static (CSS/JS) đã do WhiteNoiseMiddleware lo. Nếu sau này đặt Nginx trước thì bỏ route này.
_media_prefix = settings.MEDIA_URL.lstrip('/')
urlpatterns += [
    re_path(r'^%s(?P<path>.*)$' % re.escape(_media_prefix), serve, {'document_root': settings.MEDIA_ROOT}),
]
