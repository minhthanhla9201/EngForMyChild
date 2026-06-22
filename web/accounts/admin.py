"""Đăng ký admin cho khu tài khoản."""

from django.contrib import admin

from .models import ChildProfile, ManagePasscode


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'birth_year', 'active')
    list_filter = ('active',)
    search_fields = ('name',)


@admin.register(ManagePasscode)
class ManagePasscodeAdmin(admin.ModelAdmin):
    # Chỉ xem trạng thái; đổi passcode làm trong app (không sửa hash tay).
    list_display = ('__str__', 'is_set', 'updated_at')
    readonly_fields = ('passcode_hash', 'created_at', 'updated_at', 'created_by', 'updated_by')
