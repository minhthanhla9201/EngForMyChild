"""URL khu học từ vựng."""

from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.topic_list, name='topic_list'),
    path('topic/<slug:slug>/', views.word_list, name='word_list'),
    # Lấy audio phát âm của 1 từ (sinh + cache nếu cần) — gọi qua JS/HTMX.
    path('word/<int:pk>/audio/', views.word_audio, name='word_audio'),
]
