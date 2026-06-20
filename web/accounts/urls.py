"""URL khu tài khoản (phụ huynh)."""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    # Đăng nhập có ghi log lý do lỗi; đăng xuất dùng view sẵn của Django.
    path('login/', views.ParentLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # CRUD hồ sơ bé (theo quy ước path tiếng Anh).
    path('children/add/', views.child_add, name='child_add'),
    path('children/<int:pk>/edit/', views.child_edit, name='child_edit'),
    # Khu quản lý: tiến độ của bé (kết quả chơi + luyện phát âm).
    path('progress/', views.progress, name='progress'),
]
