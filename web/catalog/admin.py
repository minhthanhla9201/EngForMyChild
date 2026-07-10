"""Admin cho nội dung học — để phụ huynh nhập/sửa từ vựng qua web."""

from django.contrib import admin

from .models import AudioClip, Topic, Word


class WordInline(admin.TabularInline):
    model = Word
    extra = 1
    fields = ('text_en', 'text_vi', 'phonetic', 'level', 'active')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'name_vi', 'icon_static', 'icon', 'order', 'active')
    list_filter = ('active',)
    search_fields = ('name_en', 'name_vi')
    prepopulated_fields = {'slug': ('name_en',)}
    inlines = [WordInline]


class AudioClipInline(admin.TabularInline):
    model = AudioClip
    extra = 0
    fields = ('source', 'voice', 'file', 'is_default')


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('text_en', 'text_vi', 'topic', 'phonetic', 'level', 'active')
    list_filter = ('active', 'topic')
    search_fields = ('text_en', 'text_vi')
    inlines = [AudioClipInline]


@admin.register(AudioClip)
class AudioClipAdmin(admin.ModelAdmin):
    list_display = ('word', 'source', 'voice', 'is_default')
    list_filter = ('source', 'is_default')
