"""Admin cho huy hiệu (xem/sửa định nghĩa + huy hiệu bé đã mở)."""

from django.contrib import admin

from .models import Badge, ChildBadge


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name_vi', 'kind', 'threshold', 'order', 'active')
    list_filter = ('kind', 'active')
    ordering = ('order', 'threshold')


@admin.register(ChildBadge)
class ChildBadgeAdmin(admin.ModelAdmin):
    list_display = ('child', 'badge', 'created_at')
    list_filter = ('badge',)
