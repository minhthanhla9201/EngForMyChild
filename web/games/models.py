"""
Model khu trò chơi — kiến trúc "Khuôn chơi + Dữ liệu":
- GameType: cấu hình mỗi loại game (DB) → thêm game = thêm 1 module + 1 bản ghi.
- GameResult: kết quả mỗi ván chơi của bé (dữ liệu tích luỹ).

Luật chơi nằm trong module Python (games/engine/<code>.py), KHÔNG nằm trong DB.
"""

from django.db import models

from core.models import AuditedModel, YesNo


class GameType(AuditedModel):
    """Một loại game. Bật/tắt và sắp thứ tự qua DB, không cần sửa code màn chọn game."""

    code = models.SlugField('Mã game', max_length=50, unique=True)
    name_vi = models.CharField('Tên game', max_length=100)
    icon = models.CharField('Biểu tượng', max_length=50, blank=True, default='🎮')
    # Câu hướng dẫn tiếng Việt đọc cho bé khi vào màn (bé chưa biết chữ → nghe hiểu).
    # Sinh giọng bằng edge-tts (catalog.praise) + hiện chữ trong màn chơi.
    hint_vi = models.CharField('Câu hướng dẫn', max_length=150, blank=True)
    # Module xử lý luật chơi, vd 'listen_pick' (nạp từ games/engine/<module>.py).
    module = models.CharField('Module xử lý', max_length=50)
    min_words = models.PositiveSmallIntegerField('Số từ tối thiểu', default=4)
    needs_image = models.CharField('Cần hình', max_length=1, choices=YesNo.choices, default=YesNo.NO)
    needs_asr = models.CharField('Cần chấm giọng', max_length=1, choices=YesNo.choices, default=YesNo.NO)
    order = models.PositiveIntegerField('Thứ tự', default=0)
    active = models.CharField('Đang dùng', max_length=1, choices=YesNo.choices, default=YesNo.YES)

    class Meta:
        verbose_name = 'Loại game'
        verbose_name_plural = 'Loại game'
        ordering = ['order', 'name_vi']

    def __str__(self):
        return self.name_vi

    @property
    def is_active(self):
        return self.active == YesNo.YES


class GameResult(AuditedModel):
    """Kết quả một ván chơi của bé."""

    child = models.ForeignKey(
        'accounts.ChildProfile', verbose_name='Bé',
        on_delete=models.CASCADE, related_name='game_results',
    )
    game_type = models.ForeignKey(GameType, verbose_name='Loại game', on_delete=models.CASCADE,
                                  related_name='results')
    topic = models.ForeignKey('catalog.Topic', verbose_name='Chủ đề', null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='game_results')
    stars = models.PositiveSmallIntegerField('Số sao (0–3)', default=0)
    score = models.PositiveSmallIntegerField('Điểm (số câu đúng)', default=0)
    total = models.PositiveSmallIntegerField('Tổng số câu', default=0)
    duration_sec = models.PositiveIntegerField('Thời lượng (giây)', default=0)

    class Meta:
        verbose_name = 'Kết quả chơi'
        verbose_name_plural = 'Kết quả chơi'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.child.name} - {self.game_type.name_vi}: {self.stars}⭐'
