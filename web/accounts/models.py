"""Model khu tài khoản: hồ sơ bé (ChildProfile) + passcode khu quản lý."""

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from core.models import AuditedModel, YesNo


class ChildProfile(AuditedModel):
    """
    Hồ sơ một bé học. Mỗi bé thuộc về một phụ huynh (owner).

    Dữ liệu luyện tập/chơi của bé (Attempt, GameResult ở GĐ sau) gắn qua hồ sơ này.
    Avatar lưu dạng chuỗi (tên/emoji avatar bé chọn), chưa cần ImageField ở GĐ 0.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Phụ huynh',
        on_delete=models.PROTECT, related_name='children',
    )
    name = models.CharField('Tên bé', max_length=50)
    birth_year = models.PositiveSmallIntegerField('Năm sinh', null=True, blank=True)
    avatar = models.CharField('Avatar', max_length=50, blank=True, default='🐥')
    active = models.CharField('Đang dùng', max_length=1, choices=YesNo.choices, default=YesNo.YES)

    class Meta:
        verbose_name = 'Hồ sơ bé'
        verbose_name_plural = 'Hồ sơ bé'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_active_child(self):
        """Cờ Y/N → bool. So sánh '== Y' để tránh chuỗi 'N' vẫn truthy."""
        return self.active == YesNo.YES


class ManagePasscode(AuditedModel):
    """
    Passcode khu quản lý — lớp khoá thứ 2 sau đăng nhập để bé không tự vào nghịch.

    Là bản ghi cấu hình duy nhất (singleton): luôn dùng pk=1. Lưu HASH (không lưu
    mã thô) bằng cơ chế băm mật khẩu của Django. Dùng get_solo() để lấy/khởi tạo.
    """

    passcode_hash = models.CharField('Mã (đã băm)', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Passcode khu quản lý'
        verbose_name_plural = 'Passcode khu quản lý'

    def __str__(self):
        return 'Passcode khu quản lý' + ('' if self.is_set else ' (chưa đặt)')

    @classmethod
    def get_solo(cls):
        """Lấy bản ghi cấu hình duy nhất (tạo rỗng nếu chưa có)."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def is_set(self):
        """Đã đặt passcode chưa."""
        return bool(self.passcode_hash)

    def set_passcode(self, raw):
        """Đặt passcode mới (lưu dạng hash). Tự lưu DB."""
        self.passcode_hash = make_password(raw)
        self.save(update_fields=['passcode_hash', 'updated_at', 'updated_by'])

    def check_passcode(self, raw):
        """Kiểm passcode nhập vào có khớp không."""
        return self.is_set and check_password(raw, self.passcode_hash)
