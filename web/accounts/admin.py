"""Đăng ký admin cho khu tài khoản."""

from django.contrib import admin

from .models import ChildProfile


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'birth_year', 'active')
    list_filter = ('active',)
    search_fields = ('name',)
