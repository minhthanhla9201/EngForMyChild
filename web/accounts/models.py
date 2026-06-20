"""Model khu tài khoản: hồ sơ bé (ChildProfile) thuộc về phụ huynh."""

from django.conf import settings
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
