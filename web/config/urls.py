"""URL gốc dự án EngForMyChild."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # --- KHU CỦA BÉ (chỉ cần đăng nhập) ---
    path('learn/', include('catalog.urls')),       # học từ vựng
    path('speak/', include('pronunciation.urls')),  # luyện phát âm
    path('games/', include('games.urls')),          # trò chơi
    # --- KHU QUẢN LÝ NỘI DUNG (cần đăng nhập + passcode) ---
    path('manage/', include('catalog.urls_manage')),
    path('manage/', include('progress.urls_manage')),  # linh vật + huy hiệu
    # Khu tài khoản: trang chủ bé, đăng nhập, và /manage/ (dashboard, hồ sơ bé, tiến độ, passcode).
    path('', include('accounts.urls')),
]

# Phục vụ file media (audio/ảnh/ghi âm) khi chạy dev. Production để web server lo.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
