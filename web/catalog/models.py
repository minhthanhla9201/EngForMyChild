"""
Model nội dung học (kho dùng chung cho mọi bé — KHÔNG thuộc owner):
Topic (chủ đề) → Word (từ vựng) → AudioClip (audio phát âm).

Tuân thủ tương thích SQLite ↔ MySQL: cột unique/index giữ max_length ≤ 191,
luôn khai báo max_length, cờ Y/N là CharField (xem docs/ThietKeDuLieu.md 0.1).
"""

from django.db import models

from core.icons import resolve_icon_src
from core.models import AuditedModel, YesNo


class Topic(AuditedModel):
    """Chủ đề từ vựng (Animals, Colors, Family...)."""

    name_en = models.CharField('Tên (tiếng Anh)', max_length=100)
    name_vi = models.CharField('Tên (tiếng Việt)', max_length=100)
    slug = models.SlugField('Định danh', max_length=100, unique=True)
    # icon_static: đường dẫn SVG CỐ ĐỊNH trong static (vd 'icons/topic/animals.svg')
    # — commit theo repo, deploy máy khác luôn có, KHÔNG phụ thuộc font. MẶC ĐỊNH.
    icon_static = models.CharField('SVG tĩnh', max_length=120, blank=True,
                                   help_text="Đường dẫn trong static, vd icons/topic/animals.svg")
    # icon (emoji): fallback cuối + suy ra SVG offline (media).
    icon = models.CharField('Biểu tượng (emoji)', max_length=50, blank=True, default='📚')
    # icon_image: ảnh chủ đề do người quản lý upload (ƯU TIÊN cao nhất nếu có).
    icon_image = models.ImageField('Ảnh chủ đề', upload_to='images/topic/', blank=True)
    order = models.PositiveIntegerField('Thứ tự', default=0)
    active = models.CharField('Đang dùng', max_length=1, choices=YesNo.choices, default=YesNo.YES)

    class Meta:
        verbose_name = 'Chủ đề'
        verbose_name_plural = 'Chủ đề'
        ordering = ['order', 'name_en']

    def __str__(self):
        return f'{self.name_en} ({self.name_vi})'

    @property
    def is_active(self):
        # So sánh '== Y' — tránh chuỗi 'N' vẫn truthy.
        return self.active == YesNo.YES

    @property
    def icon_src(self):
        """URL icon để render <img>: ảnh upload > SVG tĩnh (repo) > SVG offline emoji > ''."""
        return resolve_icon_src(self.icon_image, self.icon_static, self.icon)


class Word(AuditedModel):
    """Một từ vựng thuộc chủ đề. Đơn vị học chính, dùng chung cho mọi game."""

    topic = models.ForeignKey(Topic, verbose_name='Chủ đề', on_delete=models.CASCADE, related_name='words')
    text_en = models.CharField('Từ (tiếng Anh)', max_length=100)
    text_vi = models.CharField('Nghĩa (tiếng Việt)', max_length=150)
    # IPA tự sinh khi trống (eng-to-ipa) — xem catalog/ipa.py.
    phonetic = models.CharField('Phiên âm (IPA)', max_length=150, blank=True)
    image = models.ImageField('Hình minh hoạ', upload_to='images/', blank=True)
    level = models.PositiveSmallIntegerField('Độ khó', default=1)
    active = models.CharField('Đang dùng', max_length=1, choices=YesNo.choices, default=YesNo.YES)

    class Meta:
        verbose_name = 'Từ vựng'
        verbose_name_plural = 'Từ vựng'
        ordering = ['topic', 'text_en']
        constraints = [
            # Trong một chủ đề không trùng từ — cũng giúp import CSV idempotent.
            models.UniqueConstraint(fields=['topic', 'text_en'], name='uniq_word_per_topic'),
        ]

    def __str__(self):
        return self.text_en

    @property
    def is_active(self):
        return self.active == YesNo.YES


class AudioClip(AuditedModel):
    """
    Audio phát âm cho một từ. Một từ có thể có nhiều clip (nhiều nguồn/giọng).
    Ưu tiên phát clip recorded/is_default; nếu chưa có thì sinh TTS rồi lưu (cache).
    """

    class Source(models.TextChoices):
        TTS = 'tts', 'Máy đọc (TTS)'
        RECORDED = 'recorded', 'Thu sẵn'

    word = models.ForeignKey(Word, verbose_name='Từ vựng', on_delete=models.CASCADE, related_name='clips')
    source = models.CharField('Nguồn', max_length=10, choices=Source.choices, default=Source.TTS)
    voice = models.CharField('Giọng', max_length=50, blank=True)
    file = models.FileField('Tệp âm thanh', upload_to='audio/')
    is_default = models.CharField('Mặc định', max_length=1, choices=YesNo.choices, default=YesNo.NO)

    class Meta:
        verbose_name = 'Audio phát âm'
        verbose_name_plural = 'Audio phát âm'
        ordering = ['word', '-is_default']

    def __str__(self):
        return f'{self.word.text_en} [{self.get_source_display()}]'

    @property
    def is_default_clip(self):
        return self.is_default == YesNo.YES
