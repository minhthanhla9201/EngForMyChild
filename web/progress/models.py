"""
Model tiến độ & huy hiệu cho bé.

- Badge: định nghĩa huy hiệu (kho CHUNG, không thuộc owner) — điều kiện mở khoá
  mô tả bằng dữ liệu (kind + threshold) để thêm huy hiệu KHÔNG cần sửa code.
- ChildBadge: huy hiệu một bé đã mở được (dữ liệu tích luỹ của bé).

Tiến độ hiển thị cho bé (tổng sao, mức cây, streak) TÍNH từ GameResult/Attempt
đã có — xem progress/service.py. Model ở đây chỉ lưu định nghĩa + trạng thái mở khoá.
"""

from django.db import models

from core.models import AuditedModel, YesNo


class Badge(AuditedModel):
    """Một huy hiệu bé có thể mở khoá. Kho chung cho mọi bé (không thuộc owner)."""

    class Kind(models.TextChoices):
        """Loại điều kiện mở khoá — quyết định 'đo' bằng chỉ số nào của bé."""
        TOTAL_STARS = 'STARS', 'Tổng số sao'        # tổng sao tích luỹ từ game
        GAMES_PLAYED = 'GAMES', 'Số lượt chơi'      # số ván game đã chơi
        WORDS_PRACTICED = 'WORDS', 'Số từ đã luyện'  # số lần luyện phát âm
        STREAK_DAYS = 'STREAK', 'Chuỗi ngày học'    # số ngày học liên tiếp

    code = models.SlugField('Mã huy hiệu', max_length=50, unique=True)
    name_vi = models.CharField('Tên huy hiệu', max_length=100)
    icon = models.CharField('Biểu tượng', max_length=50, blank=True, default='🏅')
    # Câu khích lệ ngắn hiện khi mở được (bé chưa biết chữ → cũng đọc bằng giọng ở client).
    desc_vi = models.CharField('Lời khen', max_length=150, blank=True)
    kind = models.CharField('Loại điều kiện', max_length=10, choices=Kind.choices)
    threshold = models.PositiveIntegerField('Ngưỡng đạt', default=1)
    order = models.PositiveIntegerField('Thứ tự', default=0)
    active = models.CharField('Đang dùng', max_length=1, choices=YesNo.choices, default=YesNo.YES)

    class Meta:
        verbose_name = 'Huy hiệu'
        verbose_name_plural = 'Huy hiệu'
        ordering = ['order', 'threshold']

    def __str__(self):
        return f'{self.icon} {self.name_vi}'

    @property
    def is_active(self):
        return self.active == YesNo.YES


class ChildBadge(AuditedModel):
    """Huy hiệu một bé ĐÃ mở khoá (ghi lại thời điểm để hiện 'vừa đạt')."""

    child = models.ForeignKey(
        'accounts.ChildProfile', verbose_name='Bé',
        on_delete=models.CASCADE, related_name='badges',
    )
    badge = models.ForeignKey(Badge, verbose_name='Huy hiệu', on_delete=models.CASCADE,
                              related_name='awarded')

    class Meta:
        verbose_name = 'Huy hiệu của bé'
        verbose_name_plural = 'Huy hiệu của bé'
        ordering = ['-created_at']
        # Mỗi bé chỉ mở mỗi huy hiệu 1 lần.
        constraints = [
            models.UniqueConstraint(fields=['child', 'badge'], name='uniq_child_badge'),
        ]

    def __str__(self):
        return f'{self.child.name} - {self.badge.name_vi}'
