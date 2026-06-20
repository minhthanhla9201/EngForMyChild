"""
Lệnh nhập từ vựng hàng loạt từ file CSV.

Cách dùng:
    python manage.py import_words duong/dan/words.csv
    python manage.py import_words words.csv --no-audio   # chỉ nhập từ, không sinh audio

Logic nhập nằm ở catalog/imports.py (dùng chung với màn nhập CSV qua web) —
lệnh này chỉ lo đọc file + in thống kê.
"""

from django.core.management.base import BaseCommand, CommandError

from catalog import imports as import_service


class Command(BaseCommand):
    help = 'Nhập từ vựng từ file CSV (tự sinh IPA + audio).'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', help='Đường dẫn file CSV')
        parser.add_argument('--no-audio', action='store_true',
                            help='Không sinh audio (chỉ nhập dữ liệu — nhanh, không cần mạng)')

    def handle(self, *args, **options):
        path = options['csv_path']
        make_audio = not options['no_audio']

        # Console Windows (cp932/cp1258...) có thể không in được tiếng Việt/IPA → ép UTF-8
        # để thông báo tiến độ không làm lệnh crash (UnicodeEncodeError).
        try:
            self.stdout._out.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass

        try:
            f = open(path, newline='', encoding='utf-8-sig')  # utf-8-sig: bỏ BOM của Excel
        except OSError as e:
            raise CommandError(f'Không mở được file: {e}')

        try:
            with f:
                stats = import_service.import_csv_file(
                    f, make_audio=make_audio,
                    on_progress=lambda msg: self.stdout.write(self.style.WARNING(msg)),
                )
        except import_service.ImportError_ as e:
            raise CommandError(str(e))

        self.stdout.write(self.style.SUCCESS(
            f"Xong. Chủ đề mới: {stats['created_topics']} | Từ mới: {stats['created_words']} | "
            f"Từ cập nhật: {stats['updated_words']} | Audio OK: {stats['audio_ok']} | "
            f"Audio lỗi: {stats['audio_fail']}"))
