"""
Tao LAI thu muc media/ tu du lieu trong database.

Dung khi thu muc media bi mat (xoa nham, loi o cung, doi may...)
nhung database van con -- phuc hoi file tren dia ma KHONG tao ban ghi DB trung.

CACH DUNG:
    # Chay day du (audio phat am + huong dan)
    python web/manage.py recreate_media

    # Chi tao audio phat am, bo qua huong dan
    python web/manage.py recreate_media --skip-instructions

    # Tao lai ca file da co tren dia
    python web/manage.py recreate_media --force

    # Chi xem danh sach se tao, KHONG sinh file
    python web/manage.py recreate_media --dry-run

SAU KHI CHAY XONG, chay them 2 lenh de phuc hoi het media:
    python web/manage.py fetch_images --force
    python web/manage.py gen_praise --force

LUU Y:
    - Recordings (giong doc cua be trong media/recordings/) KHONG the tao lai --
      DB chi luu duong dan file, khong luu noi dung am thanh. Can backup rieng.
    - Audio can internet (edge-tts); neu khong co mang se dung giong Windows (pyttsx3).
      Khi khong co mang, loi dong vien (praise/) se bi bo qua.
"""

import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog import tts
from catalog.audio import get_vi_instruction
from catalog.models import AudioClip, Word

logger = logging.getLogger('eng.catalog')


class Command(BaseCommand):
    help = 'Tao lai file media (audio, instructions) tu du lieu database.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Chi xem danh sach se tao, khong sinh file.')

        parser.add_argument('--skip-instructions', action='store_true',
                            help='Bo qua tao audio huong dan (instructions/).')

        parser.add_argument('--force', '-f', action='store_true',
                            help='Tao lai ca file da ton tai tren dia '
                                 '(mac dinh: chi tao file thieu).')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        skip_instructions = options['skip_instructions']

        # Windows terminal cp1252 khong hieu emoji -> chuyen sang utf-8.
        try:
            self.stdout._out.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass

        media_root = Path(settings.MEDIA_ROOT)

        # --- Kiem tra DB co du lieu khong truoc ---
        word_count = Word.objects.count()
        clip_count = AudioClip.objects.filter(source='tts').count()

        if word_count == 0:
            self.stdout.write(self.style.ERROR(
                'FAIL: Database khong co tu vung nao. '
                'Hay kiem tra lai DB hoac nhap tu vung truoc.'))
            return

        if clip_count == 0:
            self.stdout.write(self.style.WARNING(
                'WARN: Database khong co AudioClip nao (source=tts). '
                'Audio se duoc tao khi be bam "Nghe" lan dau. '
                'Neu muon tao san tat ca audio, dung --force de tao cho moi tu.'))

        # --- Dam bao thu muc ton tai ---
        for subdir in ('audio', 'instructions'):
            (media_root / subdir).mkdir(parents=True, exist_ok=True)

        # ================================================================
        # 1. Audio phat am (audio/)
        #
        # DB da co ban ghi AudioClip -> chi can tao lai file tren dia,
        # KHONG tao them ban ghi DB (tranh trung lap).
        # ================================================================
        if clip_count > 0:
            # Truong hop DB co AudioClip -> tai tao file theo dung duong dan da luu.
            clips = AudioClip.objects.filter(source='tts').select_related('word')
            self.stdout.write(f'\n[AUDIO] Audio phat am (audio/): {clip_count} ban ghi trong DB')

            if dry_run:
                for ac in clips:
                    self.stdout.write(f'   -> {ac.file}  <- "{ac.word.text_en}"')
            else:
                done = fail = skip = 0
                for ac in clips:
                    out_path = media_root / ac.file.name

                    if out_path.exists() and not force:
                        skip += 1
                        continue

                    # Ghi de file tren dia -- khong tao DB record moi.
                    provider = tts.synthesize_to_file(
                        ac.word.text_en, out_path, voice=ac.voice)
                    if provider:
                        done += 1
                        self.stdout.write(f'   [OK] {ac.file}  <- "{ac.word.text_en}"',
                                          self.style.SUCCESS)
                    else:
                        fail += 1
                        self.stdout.write(f'   [ERR] {ac.file}  <- "{ac.word.text_en}" (loi TTS)',
                                          self.style.ERROR)

                self.stdout.write(f'\n   => Da tao: {done} | Da co: {skip} | Loi: {fail}')

        else:
            # Truong hop DB KHONG co AudioClip nao -- dung --force de tao cho moi Word.
            if not force:
                self.stdout.write(self.style.WARNING(
                    '\n[AUDIO] Bo qua audio phat am (khong co AudioClip trong DB, '
                    'dung --force de tao moi cho moi tu).'))
            else:
                from catalog.audio import generate_tts_clip
                words = Word.objects.all()
                self.stdout.write(
                    f'\n[AUDIO] Audio phat am (audio/): tao MOI cho {len(words)} tu (--force)')

                if dry_run:
                    for w in words:
                        self.stdout.write(f'   -> audio/word_{w.pk}.mp3  <- "{w.text_en}"')
                else:
                    done = fail = skip = 0
                    for w in words:
                        out_path = media_root / 'audio' / f'word_{w.pk}.mp3'
                        if out_path.exists() and not force:
                            skip += 1
                            continue

                        clip = generate_tts_clip(w)
                        if clip:
                            done += 1
                            self.stdout.write(f'   [OK] {clip.file}  <- "{w.text_en}"',
                                              self.style.SUCCESS)
                        else:
                            fail += 1
                            self.stdout.write(
                                f'   [ERR] audio/word_{w.pk}.mp3  <- "{w.text_en}" (loi TTS)',
                                self.style.ERROR)

                    self.stdout.write(f'\n   => Da tao: {done} | Da co: {skip} | Loi: {fail}')

        # ================================================================
        # 2. Audio huong dan tieng Viet (instructions/)
        # ================================================================
        if not skip_instructions:
            words = Word.objects.all()
            self.stdout.write(f'\n[INST] Audio huong dan (instructions/): {len(words)} tu')

            if dry_run:
                for w in words:
                    self.stdout.write(f'   -> instructions/inst_{w.pk}.mp3  <- "{w.text_vi}"')
            else:
                done = fail = skip = 0
                for w in words:
                    out_path = media_root / 'instructions' / f'inst_{w.pk}.mp3'

                    if out_path.exists() and not force:
                        skip += 1
                        continue

                    try:
                        url = get_vi_instruction(w)
                        if url:
                            done += 1
                            self.stdout.write(
                                f'   [OK] instructions/inst_{w.pk}.mp3  <- "{w.text_vi}"',
                                self.style.SUCCESS)
                        else:
                            fail += 1
                            self.stdout.write(
                                f'   [ERR] instructions/inst_{w.pk}.mp3  <- '
                                f'"{w.text_vi}" (loi TTS)',
                                self.style.ERROR)
                    except Exception as e:
                        fail += 1
                        self.stdout.write(
                            f'   [ERR] instructions/inst_{w.pk}.mp3  <- '
                            f'"{w.text_vi}" ({e})',
                            self.style.ERROR)

                self.stdout.write(f'\n   => Da tao: {done} | Da co: {skip} | Loi: {fail}')

        # ================================================================
        # Tong ket
        # ================================================================
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('===> HOAN TAT! <==='))
        self.stdout.write('\nCac thu muc KHONG duoc xu ly boi lenh nay:')
        self.stdout.write('   - images/     -> chay: python web/manage.py fetch_images --force')
        self.stdout.write('   - praise/     -> chay: python web/manage.py gen_praise --force')
        self.stdout.write('   - recordings/ -> KHONG the tao lai (mat vinh vien)')
        self.stdout.write('\nBackup sau khi tao xong: copy thu muc web/media/ di noi khac'
                          ' de lan sau khoi chay lai.')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n(--dry-run) Chua co file nao duoc tao.'))
