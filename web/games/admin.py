"""Admin khu trò chơi."""

from django.contrib import admin

from .models import GameResult, GameType


@admin.register(GameType)
class GameTypeAdmin(admin.ModelAdmin):
    list_display = ('name_vi', 'code', 'module', 'min_words', 'needs_image', 'order', 'active')
    list_filter = ('active', 'needs_image', 'needs_asr')
    prepopulated_fields = {'code': ('name_vi',)}


@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = ('child', 'game_type', 'topic', 'stars', 'score', 'total', 'created_at')
    list_filter = ('game_type', 'child', 'stars')
