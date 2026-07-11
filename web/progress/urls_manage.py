"""
URL khu quản lý linh vật & huy hiệu (phụ huynh — đặt dưới /manage/).

Namespace 'progress_manage' để template gọi {% url 'progress_manage:...' %}.
"""

from django.urls import path

from . import views

app_name = 'progress_manage'

urlpatterns = [
    path('pets/', views.petstage_manage, name='petstage_manage'),
    path('pets/add/', views.petstage_form, name='petstage_add'),
    path('pets/<int:pk>/edit/', views.petstage_form, name='petstage_edit'),
    path('badges/', views.badge_manage, name='badge_manage'),
    path('badges/add/', views.badge_form, name='badge_add'),
    path('badges/<int:pk>/edit/', views.badge_form, name='badge_edit'),
]
