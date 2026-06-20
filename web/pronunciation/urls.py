"""URL khu luyện phát âm."""

from django.urls import path

from . import views

app_name = 'pronunciation'

urlpatterns = [
    path('', views.choose, name='choose'),
    path('<int:child_id>/<slug:slug>/', views.practice, name='practice'),
    # Nhận bản ghi giọng bé cho một từ (POST multipart).
    path('<int:child_id>/word/<int:word_id>/save/', views.save_attempt, name='save_attempt'),
]
