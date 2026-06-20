"""
Lệnh nhập từ vựng hàng loạt từ file CSV.

Cách dùng:
    python manage.py import_words duong/dan/words.csv
    python manage.py import_words words.csv --no-audio   # chỉ nhập từ, không sinh audio

CSV (có dòng tiêu đề), cột:
    topic        : tên chủ đề (tiếng Anh) — tự tạo Topic nếu chưa có
    text_en      : từ tiếng Anh (bắt buộc)
    text_vi      : nghĩa tiếng Việt
    topic_vi     : (tuỳ chọn) tên chủ đề tiếng Việt khi tạo mới
    level        : (tuỳ chọn) độ khó, mặc định 1

Đặc điểm:
    - Idempotent: chạy lại không tạo trùng (dựa UniqueConstraint topic+text_en) — cập nhật nghĩa nếu đổi.
    - Tự sinh IPA (eng-to-ipa) khi phonetic trống.
    - Tự sinh audio TTS + cache (trừ khi --no-audio). Audio dùng được offline qua pyttsx3.
"""

import csv

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from catalog import audio as audio_service
from catalog import ipa as ipa_service
from catalog.models import Topic, Word


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

        created_topics = created_words = updated_words = audio_ok = audio_fail = 0
        with f:
            reader = csv.DictReader(f)
            if 'text_en' not in (reader.fieldnames or []):
                raise CommandError("CSV thiếu cột bắt buộc 'text_en'. Tiêu đề hiện có: "
                                   f'{reader.fieldnames}')

            for i, row in enumerate(reader, start=2):  # dòng 1 là tiêu đề
                text_en = (row.get('text_en') or '').strip()
                if not text_en:
                    self.stdout.write(self.style.WARNING(f'Dòng {i}: bỏ qua (text_en trống).'))
                    continue

                topic_name = (row.get('topic') or 'General').strip()
                topic, t_created = self._get_topic(topic_name, (row.get('topic_vi') or '').strip())
                created_topics += 1 if t_created else 0

                # Idempotent: tìm theo (topic, text_en); có thì cập nhật, chưa có thì tạo.
                word, w_created = Word.objects.get_or_create(
                    topic=topic, text_en=text_en,
                    defaults={'text_vi': (row.get('text_vi') or '').strip(),
                              'level': self._to_int(row.get('level'), 1)},
                )
                if w_created:
                    created_words += 1
                else:
                    new_vi = (row.get('text_vi') or '').strip()
                    if new_vi and new_vi != word.text_vi:
                        word.text_vi = new_vi
                        word.save(update_fields=['text_vi'])
                        updated_words += 1

                # Sinh IPA nếu chưa có.
                if not word.phonetic:
                    phon = ipa_service.to_ipa(text_en)
                    if phon:
                        word.phonetic = phon
                        word.save(update_fields=['phonetic'])

                # Sinh + cache audio (nếu bật và chưa có clip).
                if make_audio and not word.clips.exists():
                    clip = audio_service.get_clip(word)
                    if clip:
                        audio_ok += 1
                    else:
                        audio_fail += 1

        self.stdout.write(self.style.SUCCESS(
            f'Xong. Chủ đề mới: {created_topics} | Từ mới: {created_words} | '
            f'Từ cập nhật: {updated_words} | Audio OK: {audio_ok} | Audio lỗi: {audio_fail}'))

    def _get_topic(self, name_en, name_vi):
        """Lấy/ tạo Topic theo slug của tên tiếng Anh (idempotent)."""
        slug = slugify(name_en)
        topic, created = Topic.objects.get_or_create(
            slug=slug,
            defaults={'name_en': name_en, 'name_vi': name_vi or name_en},
        )
        return topic, created

    @staticmethod
    def _to_int(value, default):
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return default
