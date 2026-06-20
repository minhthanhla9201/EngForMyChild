"""URL gốc dự án EngForMyChild."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Khu học từ vựng.
    path('learn/', include('catalog.urls')),
    # Khu luyện phát âm.
    path('speak/', include('pronunciation.urls')),
    # Khu trò chơi.
    path('games/', include('games.urls')),
    # Khu tài khoản đặt ở gốc (trang chủ, đăng nhập, hồ sơ bé).
    path('', include('accounts.urls')),
]

# Phục vụ file media (audio/ảnh/ghi âm) khi chạy dev. Production để web server lo.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
