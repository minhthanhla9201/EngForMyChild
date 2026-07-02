"""URL khu tài khoản: trang chủ khu của bé, đăng nhập, và khu quản lý (/manage/)."""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    # Trang chủ KHU CỦA BÉ (chỉ cần đăng nhập).
    path('', views.home, name='home'),
    # Đăng nhập có ghi log lý do lỗi; đăng xuất dùng view sẵn của Django.
    path('login/', views.ParentLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- KHU QUẢN LÝ (/manage/): vào cần đăng nhập + passcode ---
    # Mở khoá / đặt passcode lần đầu.
    path('manage/unlock/', views.manage_unlock, name='manage_unlock'),
    path('manage/lock/', views.manage_lock, name='manage_lock'),
    path('manage/passcode/change/', views.manage_passcode_change, name='manage_passcode_change'),
    # Bảng điều khiển + CRUD hồ sơ bé + tiến độ.
    path('manage/', views.dashboard, name='dashboard'),
    path('manage/children/add/', views.child_add, name='child_add'),
    path('manage/children/<int:pk>/edit/', views.child_edit, name='child_edit'),
    path('manage/children/<int:pk>/delete/', views.child_delete, name='child_delete'),
    path('manage/progress/', views.progress, name='progress'),
]
