"""
Model luyện phát âm: mỗi lần bé thu giọng một từ → một Attempt.

GĐ 2: lưu bản ghi (recording) của bé; các cột chấm điểm (asr_text/score/stars)
để trống, sẽ được điền ở GĐ 3 khi tích hợp Faster-Whisper.
"""

from django.db import models

from catalog.models import Word
from core.models import AuditedModel


class Attempt(AuditedModel):
    """Một lần bé luyện đọc một từ. Là dữ liệu tích luỹ dần vào local."""

    # Bé thực hiện. Dữ liệu của bé gắn qua ChildProfile (không dùng owner trực tiếp).
    child = models.ForeignKey(
        'accounts.ChildProfile', verbose_name='Bé',
        on_delete=models.CASCADE, related_name='attempts',
    )
    word = models.ForeignKey(Word, verbose_name='Từ', on_delete=models.CASCADE, related_name='attempts')
    recording = models.FileField('Bản ghi giọng bé', upload_to='recordings/')

    # --- Phần chấm điểm: GĐ 3 (Faster-Whisper) mới điền ---
    asr_text = models.CharField('Máy nghe được', max_length=255, blank=True)
    score = models.PositiveSmallIntegerField('Điểm khớp (0–100)', null=True, blank=True)
    stars = models.PositiveSmallIntegerField('Số sao (0–3)', null=True, blank=True)

    class Meta:
        verbose_name = 'Lần luyện phát âm'
        verbose_name_plural = 'Lần luyện phát âm'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.child.name} đọc "{self.word.text_en}"'

    @property
    def is_scored(self):
        """Đã chấm điểm chưa (GĐ 3). Dùng null check vì score có thể = 0."""
        return self.score is not None
