"""Admin cho luyện phát âm — phụ huynh xem lại bản ghi của bé."""

from django.contrib import admin

from .models import Attempt


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('child', 'word', 'score', 'stars', 'created_at')
    list_filter = ('child', 'stars')
    search_fields = ('word__text_en', 'child__name')
    readonly_fields = ('created_at', 'updated_at')
