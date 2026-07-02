"""
Seed thêm các game NHẬN DẠNG (nghe/nhìn — không cần biết chữ) cho bé chưa biết đọc.

Thêm game = thêm 1 bản ghi GameType + 1 module trong games/engine + 1 template
play_<module>.html. Tất cả đều needs_image='Y' vì lấy hình làm lựa chọn.
"""

from django.db import migrations

GAMES = [
    {
        'code': 'listen-pick-image', 'name_vi': 'Nghe & chọn hình', 'icon': '👂🖼️',
        'module': 'listen_pick_image', 'min_words': 4,
        'needs_image': 'Y', 'needs_asr': 'N', 'order': 3,
    },
    {
        'code': 'image-pick-audio', 'name_vi': 'Nhìn hình & chọn tiếng', 'icon': '🖼️🔊',
        'module': 'image_pick_audio', 'min_words': 4,
        'needs_image': 'Y', 'needs_asr': 'N', 'order': 4,
    },
    {
        'code': 'match-image-audio', 'name_vi': 'Ghép hình với tiếng', 'icon': '🃏🔊',
        'module': 'match_image_audio', 'min_words': 4,
        'needs_image': 'Y', 'needs_asr': 'N', 'order': 5,
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
        ('games', '0002_seed_game_types'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
