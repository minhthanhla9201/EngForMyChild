"""URL khu trò chơi."""

from django.urls import path

from . import views

app_name = 'games'

urlpatterns = [
    path('', views.choose, name='choose'),
    path('<int:child_id>/<slug:code>/<slug:slug>/', views.play, name='play'),
    path('<int:child_id>/<slug:code>/<slug:slug>/submit/', views.submit, name='submit'),
]
