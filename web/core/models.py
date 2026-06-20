"""
Model & tiện ích dùng chung cho toàn dự án.

- YesNo: lựa chọn cờ Y/N (KHÔNG dùng BooleanField — xem skill eng-coding mục 3).
- AuditedModel: base model mang sẵn cột audit, tự điền created_by/updated_by.
"""

from django.conf import settings
from django.db import models

from .middleware import get_current_user


class YesNo(models.TextChoices):
    """Cờ Y/N dùng chung (vd cột active). Lưu 1 ký tự — bằng nhau trên SQLite & MySQL."""
    YES = 'Y', 'Có'
    NO = 'N', 'Không'


class AuditedModel(models.Model):
    """
    Base abstract cho mọi bảng nghiệp vụ: thêm cột thời gian + người tạo/sửa.

    Bảng kế thừa KHÔNG khai báo lại các cột này. created_by/updated_by được điền
    tự động từ user đăng nhập (qua CurrentUserMiddleware) trong save() — không gán
    tay ở view. Cho phép null vì hành động của bé (chơi/luyện) không đăng nhập.
    """

    created_at = models.DateTimeField('Ngày tạo', auto_now_add=True)
    updated_at = models.DateTimeField('Ngày cập nhật', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Người tạo',
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+',  # không cần truy ngược từ User
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Người cập nhật',
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+',
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Tự điền người tạo (lần đầu) và người cập nhật (mỗi lần lưu) từ request hiện tại.
        user = get_current_user()
        if user is not None:
            if not self.pk and self.created_by_id is None:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)
