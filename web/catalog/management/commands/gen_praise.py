"""
Sinh sẵn GIỌNG ĐỘNG VIÊN tiếng Việt (mp3) bằng edge-tts để cache.

Chạy một lần lúc setup (cần internet cho edge-tts), sau đó khu của bé phát offline:
    python web/manage.py gen_praise
    python web/manage.py gen_praise --force   # sinh lại tất cả (khi đổi câu/giọng)

Thêm câu động viên: sửa PRAISE_LINES trong catalog/praise.py rồi chạy lại lệnh này.
"""

from django.core.management.base import BaseCommand

from catalog import praise


class Command(BaseCommand):
    help = 'Sinh mp3 các câu động viên tiếng Việt (edge-tts) để cache cho khu của bé.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Sinh lại cả những file đã có (khi đổi câu/giọng).')

    def handle(self, *args, **options):
        gen, skip, fail = praise.generate_all(force=options['force'])
        self.stdout.write(self.style.SUCCESS(
            f'Xong: sinh moi {gen}, bo qua {skip}, loi {fail}.'))
        if fail:
            self.stdout.write(self.style.WARNING(
                'Co cau sinh loi (edge-tts) — chay lai lenh de thu tiep (can internet).'))
