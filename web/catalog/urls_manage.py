"""
URL khu quản lý nội dung học (cho phụ huynh — đặt dưới /manage/).

Tách khỏi catalog/urls.py (khu của bé) để 2 khu có tiền tố URL riêng biệt.
Dùng chung namespace 'catalog' (app_name) để template gọi {% url 'catalog:...' %}.
"""

from django.urls import path

from . import views

app_name = 'catalog_manage'

urlpatterns = [
    path('topics/', views.topic_manage, name='topic_manage'),
    path('topics/add/', views.topic_form, name='topic_add'),
    path('topics/<int:pk>/edit/', views.topic_form, name='topic_edit'),
    path('words/', views.word_manage, name='word_manage'),
    path('words/add/', views.word_form, name='word_add'),
    path('words/<int:pk>/edit/', views.word_form, name='word_edit'),
    path('import/', views.word_import, name='word_import'),
]
