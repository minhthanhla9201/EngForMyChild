"""Admin cho linh vật + huy hiệu (xem/sửa định nghĩa + huy hiệu bé đã mở)."""

from django.contrib import admin

from .models import Badge, ChildBadge, PetStage


@admin.register(PetStage)
class PetStageAdmin(admin.ModelAdmin):
    list_display = ('threshold', 'name_vi', 'description', 'level', 'icon_static', 'emoji', 'order', 'active')
    list_filter = ('active',)
    ordering = ('threshold',)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name_vi', 'icon_static', 'icon', 'kind', 'threshold', 'order', 'active')
    list_filter = ('kind', 'active')
    ordering = ('order', 'threshold')


@admin.register(ChildBadge)
class ChildBadgeAdmin(admin.ModelAdmin):
    list_display = ('child', 'badge', 'created_at')
    list_filter = ('badge',)
