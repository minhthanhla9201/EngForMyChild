"""
Model tiến độ & huy hiệu cho bé.

- Badge: định nghĩa huy hiệu (kho CHUNG, không thuộc owner) — điều kiện mở khoá
  mô tả bằng dữ liệu (kind + threshold) để thêm huy hiệu KHÔNG cần sửa code.
- ChildBadge: huy hiệu một bé đã mở được (dữ liệu tích luỹ của bé).

Tiến độ hiển thị cho bé (tổng sao, mức cây, streak) TÍNH từ GameResult/Attempt
đã có — xem progress/service.py. Model ở đây chỉ lưu định nghĩa + trạng thái mở khoá.
"""

from django.db import models

from core.icons import emoji_svg_path
from core.models import AuditedModel, YesNo


def _resolve_icon_src(image, icon_static, emoji):
    """
    URL icon để render <img>, theo thứ tự ưu tiên (dùng chung PetStage/Badge):
    1) ảnh upload (media) — phụ huynh tự đặt riêng;
    2) SVG tĩnh trong static (repo) — MẶC ĐỊNH, commit theo mã nguồn nên deploy
       máy khác luôn có, không cần mạng, không phụ thuộc font;
    3) SVG offline của emoji trong media (nếu đã fetch);
    4) '' → template hiển thị ký tự emoji (fallback cuối).
    """
    if image:
        return image.url
    if icon_static:
        from django.templatetags.static import static
        return static(icon_static)
    rel = emoji_svg_path(emoji)
    if rel:
        from django.conf import settings
        return f'{settings.MEDIA_URL}{rel}'
    return ''


class PetStage(AuditedModel):
    """
    Một mốc "linh vật lớn dần" theo tổng sao (hạt mầm → cây ra hoa...).

    TÁCH KHỎI code (trước đây hardcode PET_STAGES trong service.py) để phụ huynh
    tự đổi mốc/icon qua trang quản lý — dữ liệu tách rời code (skill §10.2).
    Icon KHÔNG phụ thuộc font: ưu tiên ảnh upload, nếu không thì dùng SVG offline
    của emoji (xem icon_src). Bé chưa biết chữ → nhìn icon là hiểu lớn lên.
    """

    threshold = models.PositiveIntegerField('Ngưỡng sao', unique=True)
    name_vi = models.CharField('Tên mốc', max_length=100)
    # icon_static: đường dẫn SVG CỐ ĐỊNH trong static (vd 'icons/pet/tree.svg') —
    # commit theo repo, deploy máy khác luôn có, KHÔNG phụ thuộc mạng/font. Ưu tiên
    # sau ảnh upload. Là nguồn icon MẶC ĐỊNH của app.
    icon_static = models.CharField('SVG tĩnh', max_length=120, blank=True,
                                   help_text="Đường dẫn trong static, vd icons/pet/tree.svg")
    # emoji: fallback cuối + để suy ra SVG offline (media) khi không có static/ảnh.
    emoji = models.CharField('Emoji', max_length=20, blank=True, default='🌱')
    # image: ảnh linh vật do phụ huynh upload (ƯU TIÊN cao nhất nếu có).
    image = models.ImageField('Ảnh linh vật', upload_to='images/pet/', blank=True)
    order = models.PositiveIntegerField('Thứ tự', default=0)
    active = models.CharField('Đang dùng', max_length=1, choices=YesNo.choices, default=YesNo.YES)

    class Meta:
        verbose_name = 'Linh vật (mốc lớn dần)'
        verbose_name_plural = 'Linh vật (mốc lớn dần)'
        ordering = ['threshold']

    def __str__(self):
        return f'{self.threshold}⭐ {self.name_vi}'

    @property
    def is_active(self):
        return self.active == YesNo.YES

    @property
    def icon_src(self):
        """URL icon để render <img>: ảnh upload > SVG tĩnh (repo) > SVG offline emoji > ''."""
        return _resolve_icon_src(self.image, self.icon_static, self.emoji)


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
    # icon_static: đường dẫn SVG CỐ ĐỊNH trong static (vd 'icons/badge/stars-10.svg')
    # — commit theo repo, deploy máy khác luôn có. Nguồn icon MẶC ĐỊNH của app.
    icon_static = models.CharField('SVG tĩnh', max_length=120, blank=True,
                                   help_text="Đường dẫn trong static, vd icons/badge/stars-10.svg")
    # icon (emoji): fallback cuối + để suy ra SVG offline (media).
    icon = models.CharField('Biểu tượng (emoji)', max_length=50, blank=True, default='🏅')
    # icon_image: ảnh huy hiệu do phụ huynh upload (ƯU TIÊN cao nhất nếu có).
    icon_image = models.ImageField('Ảnh huy hiệu', upload_to='images/badge/', blank=True)
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

    @property
    def icon_src(self):
        """URL icon để render <img>: ảnh upload > SVG tĩnh (repo) > SVG offline emoji > ''."""
        return _resolve_icon_src(self.icon_image, self.icon_static, self.icon)


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
