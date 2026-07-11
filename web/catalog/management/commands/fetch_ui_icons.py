"""
Tải SVG offline cho các EMOJI GIAO DIỆN cố định (linh vật, huy hiệu, icon HTML).

VÌ SAO: các emoji này trước đây nhúng thô → render bằng font hệ thống, deploy sang
máy thiếu font sẽ lỗi. Tải SVG Twemoji về media/images/ (cùng cơ chế fetch_images)
để render bằng <img>, không phụ thuộc font. Chạy MỘT LẦN sau khi migrate/seed.

Cách dùng:
    python manage.py fetch_ui_icons              # tải các SVG còn thiếu
    python manage.py fetch_ui_icons --offline    # chỉ kiểm tra, không tải mạng

Nguồn emoji cần tải gồm:
- Emoji của PetStage (linh vật) và Badge (huy hiệu) trong DB.
- Danh sách emoji tĩnh dùng thẳng trong template (STATIC_UI_EMOJIS).

Giấy phép: Twemoji CC-BY 4.0.
"""

import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand

from core.icons import emoji_to_filename
from progress.models import Badge, PetStage

logger = logging.getLogger('eng.catalog')

# CDN Twemoji (khối màu đầy đặn) — tên file chữ thường.
CDN = 'https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/svg/{name}.svg'

# Emoji viết THẲNG trong template khu bé (kid_home.html...) — cần có SVG offline.
# Thêm emoji tĩnh mới vào đây khi dùng trong template.
STATIC_UI_EMOJIS = ['🏅', '🔒', '⭐', '🔥', '🎉', '🌟', '✨', '👑', '🎮', '🕹️',
                    '🎤', '🗣️', '🏆', '📚', '🔊']


class Command(BaseCommand):
    help = 'Tải SVG offline cho emoji giao diện (linh vật, huy hiệu, icon tĩnh).'

    def add_arguments(self, parser):
        parser.add_argument('--offline', action='store_true',
                            help='Chỉ kiểm tra file có sẵn, không tải mạng.')

    def handle(self, *args, **options):
        offline = options['offline']
        try:
            self.stdout._out.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass

        out_dir = settings.MEDIA_ROOT / 'images'
        out_dir.mkdir(parents=True, exist_ok=True)

        # Gom emoji từ DB (linh vật + huy hiệu) và danh sách tĩnh, khử trùng.
        emojis = set(STATIC_UI_EMOJIS)
        emojis.update(PetStage.objects.exclude(emoji='').values_list('emoji', flat=True))
        emojis.update(Badge.objects.exclude(icon='').values_list('icon', flat=True))

        stats = {'have': 0, 'downloaded': 0, 'fail': 0}
        for emoji in sorted(emojis):
            fname = emoji_to_filename(emoji)
            if not fname:
                continue
            abs_path = out_dir / f'{fname}.svg'
            if abs_path.exists():
                stats['have'] += 1
                continue
            if offline:
                stats['fail'] += 1
                continue
            if self._download(fname, abs_path):
                stats['downloaded'] += 1
            else:
                stats['fail'] += 1

        self.stdout.write(self.style.SUCCESS(
            f"Xong. Đã có: {stats['have']} | Tải mới: {stats['downloaded']} | "
            f"Thiếu/lỗi: {stats['fail']}"))

    def _download(self, name, abs_path):
        """Tải một SVG Twemoji từ CDN, lưu ra abs_path. Trả True nếu thành công."""
        url = CDN.format(name=name.lower())
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'eng-fetch-ui-icons'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            abs_path.write_bytes(data)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            logger.warning('Không tải được icon %s (%s): %s', name, url, e)
            return False
