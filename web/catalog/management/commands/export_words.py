"""
Lệnh xuất từ vựng ra file CSV (backup).

Cách dùng:
    python manage.py export_words                 # in ra màn hình
    python manage.py export_words words_backup.csv # ghi ra file

File xuất khớp định dạng của import_words → nạp lại được để khôi phục:
    python manage.py import_words words_backup.csv --no-audio

Logic xuất nằm ở catalog/imports.py (dùng chung với nút Xuất CSV trên web).
"""

from django.core.management.base import BaseCommand, CommandError

from catalog import imports as import_service


class Command(BaseCommand):
    help = 'Xuất toàn bộ từ vựng ra CSV (backup, nạp lại được qua import_words).'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', nargs='?', default=None,
                            help='Đường dẫn file CSV để ghi (bỏ trống → in ra màn hình)')

    def handle(self, *args, **options):
        csv_text = import_service.export_words()
        path = options['csv_path']

        # Ép UTF-8 để in nội dung/thông báo tiếng Việt không crash trên console Windows
        # (cp932/cp1258...). Áp cho cả nhánh in ra màn hình lẫn thông báo thành công.
        try:
            self.stdout._out.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass

        if not path:
            self.stdout.write(csv_text)
            return

        try:
            # csv_text đã kèm sẵn BOM → ghi utf-8 thường (dùng utf-8-sig sẽ thành BOM kép).
            # newline='' để không thêm dòng trống thừa trên Windows.
            with open(path, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_text)
        except OSError as e:
            raise CommandError(f'Không ghi được file: {e}')

        self.stdout.write(self.style.SUCCESS(f'Đã xuất từ vựng ra {path}'))
