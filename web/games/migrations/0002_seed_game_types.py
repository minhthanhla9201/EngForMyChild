"""Seed các loại game ban đầu (GĐ 4). Thêm game mới chỉ cần thêm bản ghi tương tự + module."""

from django.db import migrations

# Danh sách game ban đầu. needs_image='Y' → game chỉ dùng từ có hình.
GAMES = [
    {
        'code': 'listen-pick', 'name_vi': 'Nghe & chọn', 'icon': '👂',
        'module': 'listen_pick', 'min_words': 4, 'needs_image': 'N', 'order': 1,
    },
    {
        'code': 'match-pairs', 'name_vi': 'Lật thẻ tìm cặp', 'icon': '🃏',
        'module': 'match_pairs', 'min_words': 4, 'needs_image': 'N', 'order': 2,
    },
]


def seed(apps, schema_editor):
    GameType = apps.get_model('games', 'GameType')
    for g in GAMES:
        # Idempotent theo code — chạy lại không tạo trùng.
        GameType.objects.update_or_create(code=g['code'], defaults=g)


def unseed(apps, schema_editor):
    GameType = apps.get_model('games', 'GameType')
    GameType.objects.filter(code__in=[g['code'] for g in GAMES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
