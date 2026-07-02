"""
Tải hình minh hoạ (emoji Twemoji SVG) cho từ vựng và gán vào Word.image.

Cách dùng:
    python manage.py fetch_images              # tải cho từ CHƯA có hình
    python manage.py fetch_images --force      # tải lại cho MỌI từ (kể cả đã có)
    python manage.py fetch_images --offline    # chỉ gán từ SVG đã có sẵn trong media (không tải mạng)

Cơ chế:
- Ánh xạ text_en → emoji ở catalog/emoji_map.py (soạn tay cho sát nghĩa).
- Đổi emoji → mã codepoint → tên file '<CP>.svg' (chuẩn Twemoji, vd 🐱 → 1F431.svg),
  khớp bộ SVG đang có sẵn trong media/images/.
- Nếu file chưa có: tải từ CDN jsdelivr (Twemoji, giấy phép CC-BY 4.0) rồi lưu lại.
  Tải MỘT LẦN; sau đó chạy học hoàn toàn offline (file đã nằm trên máy).
- Gán word.image = 'images/<CP>.svg'. Idempotent: chạy lại không tải trùng.

KHÔNG cần mạng khi học — chỉ cần mạng lúc chạy lệnh này để tải các SVG còn thiếu.
"""

import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog.emoji_map import EMOJI_MAP
from catalog.models import Word

logger = logging.getLogger('eng.catalog')

# CDN Twemoji (SVG màu). Tải 1 lần rồi lưu offline.
CDN = 'https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/svg/{name}.svg'


def emoji_to_filename(emoji):
    """
    Đổi emoji → tên file Twemoji: các codepoint nối bằng '-', HOA, bỏ VS16 (FE0F).

    VD '🐱' → '1F431'; '☂️' (U+2602 U+FE0F) → '2602'. Twemoji bỏ FE0F trong tên file
    (trừ vài emoji keycap có 20E3 — hiếm trong bộ này nên không xử lý riêng).
    """
    cps = [f'{ord(ch):X}' for ch in emoji if ord(ch) != 0xFE0F]
    return '-'.join(cps)


class Command(BaseCommand):
    help = 'Tải hình minh hoạ (Twemoji SVG) cho từ vựng và gán vào Word.image.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Gán lại cho cả từ đã có hình.')
        parser.add_argument('--offline', action='store_true',
                            help='Chỉ dùng SVG có sẵn trong media, không tải mạng.')

    def handle(self, *args, **options):
        force = options['force']
        offline = options['offline']

        try:
            self.stdout._out.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass

        images_dir = settings.MEDIA_ROOT / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)

        stats = {'assigned': 0, 'downloaded': 0, 'skipped_have': 0,
                 'no_emoji': 0, 'download_fail': 0}

        for word in Word.objects.all():
            if word.image and not force:
                stats['skipped_have'] += 1
                continue

            emoji = EMOJI_MAP.get(word.text_en.lower())
            if not emoji:
                stats['no_emoji'] += 1
                continue

            fname = emoji_to_filename(emoji)
            rel_path = f'images/{fname}.svg'
            abs_path = images_dir / f'{fname}.svg'

            # Tải SVG nếu chưa có trên đĩa (và không ở chế độ offline).
            if not abs_path.exists():
                if offline:
                    stats['download_fail'] += 1
                    continue
                if not self._download(fname, abs_path):
                    stats['download_fail'] += 1
                    continue
                stats['downloaded'] += 1

            # Gán đường dẫn (chỉ lưu tham chiếu, giống import CSV).
            word.image = rel_path
            word.save(update_fields=['image'])
            stats['assigned'] += 1

        self.stdout.write(self.style.SUCCESS(
            f"Xong. Gán hình: {stats['assigned']} | Tải mới: {stats['downloaded']} | "
            f"Đã có hình (bỏ qua): {stats['skipped_have']} | "
            f"Không có emoji: {stats['no_emoji']} | Tải lỗi: {stats['download_fail']}"))

    def _download(self, name, abs_path):
        """Tải một SVG từ CDN, lưu ra abs_path. Trả True nếu thành công."""
        url = CDN.format(name=name.lower())  # Twemoji đặt tên file bằng chữ THƯỜNG
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'eng-fetch-images'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            abs_path.write_bytes(data)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            logger.warning('Không tải được emoji %s: %s', name, e)
            return False
