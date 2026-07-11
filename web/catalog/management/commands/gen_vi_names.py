"""
Sinh sẵn AUDIO ĐỌC TÊN TIẾNG VIỆT của từ (mp3, edge-tts) để cache offline.

Dùng cho GAME có hình: bé chưa biết chữ, chạm vào hình sẽ nghe tên hình ("con mèo").
Chạy một lần lúc setup (cần internet cho edge-tts), sau đó khu của bé phát offline:
    python web/manage.py gen_vi_names            # sinh cho từ CHƯA có file
    python web/manage.py gen_vi_names --force     # sinh lại tất cả (khi đổi giọng)
    python web/manage.py gen_vi_names --images-only  # chỉ từ CÓ ẢNH (dùng trong game hình)

Tên/giọng/đường dẫn cache do catalog.audio.get_vi_name lo (media/names/name_<pk>.mp3).
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog import audio as audio_service
from catalog.models import Word


class Command(BaseCommand):
    help = 'Sinh mp3 đọc tên tiếng Việt của từ (edge-tts) để cache cho game hình.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Sinh lại cả file đã có (khi đổi giọng).')
        parser.add_argument('--images-only', action='store_true',
                            help='Chỉ sinh cho từ CÓ ẢNH (đủ dùng cho game hình).')

    def handle(self, *args, **options):
        try:
            self.stdout._out.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass

        words = Word.objects.filter(active='Y')
        if options['images_only']:
            words = words.exclude(image='')

        gen = skip = fail = 0
        for word in words:
            if not word.text_vi:
                continue
            # get_vi_name idempotent (đã có file → trả URL, không sinh lại) trừ khi --force.
            if options['force']:
                out = settings.MEDIA_ROOT / 'names' / f'name_{word.pk}.mp3'
                if out.exists():
                    out.unlink()
            url = audio_service.get_vi_name(word)
            if url is None:
                fail += 1
            else:
                # Phân biệt sinh mới / đã có: get_vi_name không báo, nên đếm gộp là "xử lý".
                gen += 1

        self.stdout.write(self.style.SUCCESS(
            f'Xong: xu ly {gen} tu, loi {fail}. (skip {skip})'))
        if fail:
            self.stdout.write(self.style.WARNING(
                'Co tu sinh loi (edge-tts) — chay lai de thu tiep (can internet).'))
