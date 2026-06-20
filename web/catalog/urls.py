"""URL khu học từ vựng."""

from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.topic_list, name='topic_list'),
    path('topic/<slug:slug>/', views.word_list, name='word_list'),
    # Lấy audio phát âm của 1 từ (sinh + cache nếu cần) — gọi qua JS/HTMX.
    path('word/<int:pk>/audio/', views.word_audio, name='word_audio'),

    # --- Khu quản lý (phụ huynh): CRUD chủ đề / từ vựng + nhập CSV ---
    path('manage/topics/', views.topic_manage, name='topic_manage'),
    path('manage/topics/add/', views.topic_form, name='topic_add'),
    path('manage/topics/<int:pk>/edit/', views.topic_form, name='topic_edit'),
    path('manage/words/', views.word_manage, name='word_manage'),
    path('manage/words/add/', views.word_form, name='word_add'),
    path('manage/words/<int:pk>/edit/', views.word_form, name='word_edit'),
    path('manage/import/', views.word_import, name='word_import'),
]
