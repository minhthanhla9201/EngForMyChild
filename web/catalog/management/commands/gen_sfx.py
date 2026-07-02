"""
Sinh sẵn các file âm thanh hiệu ứng (WAV) cho khu của bé — CHẤT LƯỢNG hơn tiếng
oscillator thô của Web Audio, KHÔNG cần internet, KHÔNG lo bản quyền.

    python web/manage.py gen_sfx
    python web/manage.py gen_sfx --force

Tạo 3 file trong static/sfx/:
  correct.wav — chuông vui (hợp âm trưởng ngân, có vang) khi bé làm đúng
  wrong.wav   — 'oops' nhẹ (2 nốt đi xuống, mềm) khi bé sai — không gắt
  cheer.wav   — fanfare ngắn khi thắng ván

Chỉ dùng thư viện chuẩn (math, struct, wave). Sinh 1 lần; file nhỏ, nhúng vào
static để chạy offline.
"""

import math
import struct
import wave

from django.conf import settings
from django.core.management.base import BaseCommand

SAMPLE_RATE = 44100
AMP = 0.28  # biên độ tổng (tránh vỡ tiếng), giữ êm cho tai bé


def _tone(freq, t, decay):
    """Một nốt: sóng sin + hài bậc 2 nhẹ (ấm hơn sin thuần), tắt dần theo decay."""
    env = math.exp(-decay * t)
    base = math.sin(2 * math.pi * freq * t)
    harm = 0.25 * math.sin(2 * math.pi * freq * 2 * t)  # hài → tiếng dày, giống chuông
    return env * (base + harm)


def _render(notes, total_dur, reverb=0.0):
    """
    Trộn nhiều nốt thành mảng mẫu. `notes` = [(freq, start, decay, gain), ...].
    reverb>0: thêm một bản vọng nhẹ (delay) cho có không gian.
    """
    n = int(SAMPLE_RATE * total_dur)
    buf = [0.0] * n
    for freq, start, decay, gain in notes:
        s0 = int(start * SAMPLE_RATE)
        for i in range(s0, n):
            t = (i - s0) / SAMPLE_RATE
            buf[i] += gain * _tone(freq, t, decay)

    if reverb > 0:
        delay = int(0.08 * SAMPLE_RATE)  # vọng 80ms
        for i in range(delay, n):
            buf[i] += reverb * buf[i - delay]

    # Chuẩn hoá về [-AMP, AMP] để không vỡ tiếng.
    peak = max((abs(x) for x in buf), default=1.0) or 1.0
    scale = AMP / peak
    return [x * scale for x in buf]


def _save_wav(path, samples):
    """Ghi mảng float [-1,1] ra WAV 16-bit mono."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        frames = b''.join(struct.pack('<h', int(max(-1, min(1, s)) * 32767)) for s in samples)
        w.writeframes(frames)


# Tần số các nốt (Hz) — dùng gam Đô trưởng cho vui tai.
C5, E5, G5, C6, E6, G6 = 523.25, 659.25, 783.99, 1046.50, 1318.51, 1567.98
G4, E4 = 392.00, 329.63


def build_correct():
    """Chuông vui: hợp âm Đô trưởng rải nhanh rồi ngân, có vang nhẹ."""
    notes = [
        (C5, 0.00, 5, 0.9),
        (E5, 0.05, 5, 0.9),
        (G5, 0.10, 4, 0.9),
        (C6, 0.15, 3, 1.0),  # nốt cao chốt, lấp lánh
    ]
    return _render(notes, 1.0, reverb=0.35)


def build_wrong():
    """'Oops' nhẹ nhàng: 2 nốt đi xuống, mềm, KHÔNG chói (không phạt bé)."""
    notes = [
        (G4, 0.00, 6, 0.9),
        (E4, 0.12, 6, 0.9),
    ]
    return _render(notes, 0.6, reverb=0.15)


def build_cheer():
    """Fanfare thắng cuộc: chuỗi nốt đi lên + hợp âm chốt ngân, vang nhiều hơn."""
    notes = [
        (C5, 0.00, 6, 0.8),
        (E5, 0.10, 6, 0.8),
        (G5, 0.20, 6, 0.8),
        (C6, 0.30, 4, 0.9),
        # Hợp âm chốt: Đô–Mi–Sol cao cùng ngân.
        (C6, 0.45, 2.5, 0.9),
        (E6, 0.45, 2.5, 0.9),
        (G6, 0.45, 2.5, 1.0),
    ]
    return _render(notes, 1.6, reverb=0.4)


class Command(BaseCommand):
    help = 'Sinh các file âm thanh hiệu ứng (WAV) cho khu của bé vào static/sfx/.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Ghi đè file đã có.')

    def handle(self, *args, **options):
        out_dir = settings.BASE_DIR / 'static' / 'sfx'
        builders = {
            'correct.wav': build_correct,
            'wrong.wav': build_wrong,
            'cheer.wav': build_cheer,
        }
        made = skipped = 0
        for name, fn in builders.items():
            path = out_dir / name
            if path.exists() and not options['force']:
                skipped += 1
                continue
            _save_wav(path, fn())
            made += 1
            self.stdout.write(f'  [tao] {name}')
        self.stdout.write(self.style.SUCCESS(
            f'Xong: tao {made}, bo qua {skipped} (dung --force de ghi de).'))
