"""Seed câu hướng dẫn (hint_vi) cho các game để đọc giọng cho bé khi vào màn."""

from django.db import migrations

# code game → câu hướng dẫn (khớp câu đang hiển thị trong template play_*.html).
HINTS = {
    'listen-pick': 'Nghe rồi chọn từ đúng nhé!',
    'match-pairs': 'Lật hai thẻ để tìm cặp giống nhau nhé!',
    'listen-pick-image': 'Nghe rồi chạm vào hình đúng nhé!',
    'image-pick-audio': 'Nhìn hình, chạm loa để nghe rồi chọn tiếng đúng nhé!',
    'match-image-audio': 'Lật thẻ hình và thẻ loa để ghép đúng nhé!',
}


def seed(apps, schema_editor):
    GameType = apps.get_model('games', 'GameType')
    for code, hint in HINTS.items():
        GameType.objects.filter(code=code).update(hint_vi=hint)


def unseed(apps, schema_editor):
    GameType = apps.get_model('games', 'GameType')
    GameType.objects.filter(code__in=HINTS).update(hint_vi='')


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0004_gametype_hint_vi'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
