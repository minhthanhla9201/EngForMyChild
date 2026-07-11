"""
Tải hình minh hoạ (emoji SVG) cho từ vựng và gán vào Word.image.

Cách dùng:
    python manage.py fetch_images                       # Twemoji, cho từ CHƯA có hình
    python manage.py fetch_images --force               # gán lại cho MỌI từ
    python manage.py fetch_images --offline             # chỉ dùng SVG có sẵn (không tải mạng)
    python manage.py fetch_images --style openmoji --words cat,dog,apple --force
                                                        # thay riêng vài từ bằng OpenMoji (nét vẽ đẹp hơn)

Hai bộ hình (chọn qua --style):
- twemoji  : emoji Twitter, khối màu đầy đặn (mặc định) → lưu media/images/<CP>.svg
- openmoji : emoji vẽ tay OpenMoji, phong cách hoạt hình mảnh → lưu media/images/openmoji/<CP>.svg
  Hai bộ để thư mục KHÁC nhau nên không đè lên nhau; đổi qua lại thoải mái.

Cơ chế:
- Ánh xạ text_en → emoji ở catalog/emoji_map.py (soạn tay cho sát nghĩa).
- Đổi emoji → mã codepoint → tên file '<CP>.svg' (vd 🐱 → 1F431.svg).
- Tải từ CDN jsdelivr MỘT LẦN rồi lưu offline → sau đó học không cần mạng.
- Gán word.image = đường dẫn tương ứng. Idempotent: chạy lại không tải trùng.
- --words: chỉ áp cho các từ liệt kê (ngăn cách bằng dấu phẩy). Bỏ trống = mọi từ.

Giấy phép: Twemoji CC-BY 4.0; OpenMoji CC BY-SA 4.0.
"""

import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog.emoji_map import EMOJI_MAP
from catalog.models import Word
from core.icons import emoji_to_filename  # nguồn sự thật chung (dùng lại, không lặp)

logger = logging.getLogger('eng.catalog')

# Cấu hình mỗi bộ hình: URL CDN + thư mục con lưu trong media/images/.
STYLES = {
    'twemoji': {
        'cdn': 'https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/svg/{name}.svg',
        'subdir': '',  # media/images/<CP>.svg (giữ tương thích bộ cũ)
    },
    'openmoji': {
        # unpkg ổn định hơn jsdelivr khi tải loạt (jsdelivr hay 403). Tên file OpenMoji viết HOA.
        'cdn': 'https://unpkg.com/openmoji@15.0.0/color/svg/{name}.svg',
        'subdir': 'openmoji',  # media/images/openmoji/<CP>.svg
        'upper': True,  # CDN dùng tên file chữ HOA (khác Twemoji dùng thường)
    },
}


class Command(BaseCommand):
    help = 'Tải hình minh hoạ (emoji SVG) cho từ vựng và gán vào Word.image.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Gán lại cho cả từ đã có hình.')
        parser.add_argument('--offline', action='store_true',
                            help='Chỉ dùng SVG có sẵn trong media, không tải mạng.')
        parser.add_argument('--style', choices=sorted(STYLES), default='twemoji',
                            help='Bộ hình: twemoji (mặc định) hoặc openmoji (nét vẽ đẹp hơn).')
        parser.add_argument('--words', default='',
                            help='Chỉ áp cho các từ này (text_en, ngăn cách bằng dấu phẩy). '
                                 'Bỏ trống = mọi từ.')

    def handle(self, *args, **options):
        force = options['force']
        offline = options['offline']
        style = options['style']
        cfg = STYLES[style]

        # Lọc theo danh sách từ nếu có (chuẩn hoá chữ thường, bỏ khoảng trắng).
        only = {w.strip().lower() for w in options['words'].split(',') if w.strip()}

        try:
            self.stdout._out.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass

        # Thư mục lưu theo bộ hình (openmoji có thư mục con riêng).
        img_root = settings.MEDIA_ROOT / 'images'
        out_dir = img_root / cfg['subdir'] if cfg['subdir'] else img_root
        out_dir.mkdir(parents=True, exist_ok=True)
        rel_prefix = f"images/{cfg['subdir']}/" if cfg['subdir'] else 'images/'

        stats = {'assigned': 0, 'downloaded': 0, 'skipped_have': 0,
                 'skipped_filter': 0, 'no_emoji': 0, 'download_fail': 0}

        for word in Word.objects.all():
            if only and word.text_en.lower() not in only:
                stats['skipped_filter'] += 1
                continue
            if word.image and not force:
                stats['skipped_have'] += 1
                continue

            emoji = EMOJI_MAP.get(word.text_en.lower())
            if not emoji:
                stats['no_emoji'] += 1
                continue

            fname = emoji_to_filename(emoji)
            rel_path = f'{rel_prefix}{fname}.svg'
            abs_path = out_dir / f'{fname}.svg'

            # Tải SVG nếu chưa có trên đĩa (và không ở chế độ offline).
            if not abs_path.exists():
                if offline:
                    stats['download_fail'] += 1
                    continue
                if not self._download(cfg['cdn'], fname, abs_path, cfg.get('upper', False)):
                    stats['download_fail'] += 1
                    continue
                stats['downloaded'] += 1

            # Gán đường dẫn (chỉ lưu tham chiếu, giống import CSV).
            word.image = rel_path
            word.save(update_fields=['image'])
            stats['assigned'] += 1

        self.stdout.write(self.style.SUCCESS(
            f"Xong ({style}). Gán hình: {stats['assigned']} | Tải mới: {stats['downloaded']} | "
            f"Đã có hình (bỏ qua): {stats['skipped_have']} | Ngoài danh sách: {stats['skipped_filter']} | "
            f"Không có emoji: {stats['no_emoji']} | Tải lỗi: {stats['download_fail']}"))

    def _download(self, cdn, name, abs_path, upper=False):
        """Tải một SVG từ CDN, lưu ra abs_path. Trả True nếu thành công."""
        # Twemoji đặt tên file chữ thường; OpenMoji chữ HOA (upper=True).
        url = cdn.format(name=name.upper() if upper else name.lower())
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'eng-fetch-images'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            abs_path.write_bytes(data)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            logger.warning('Không tải được emoji %s (%s): %s', name, url, e)
            return False
