"""Seed huy hiệu ban đầu. Thêm huy hiệu mới = thêm bản ghi tương tự (dữ liệu, không sửa code)."""

from django.db import migrations

# (code, tên, icon, lời khen, loại điều kiện, ngưỡng, thứ tự)
# Loại: STARS=tổng sao · GAMES=lượt chơi · WORDS=lần luyện · STREAK=chuỗi ngày.
BADGES = [
    ('first-star',   'Ngôi sao đầu tiên', '⭐', 'Bé được sao đầu tiên rồi!', 'STARS',  1,   1),
    ('stars-10',     'Mười ngôi sao',     '🌟', 'Bé đã có 10 sao, giỏi quá!', 'STARS', 10,   2),
    ('stars-25',     'Nhà sưu tầm sao',   '✨', 'Hai mươi lăm sao lận!',       'STARS', 25,   3),
    ('stars-50',     'Vua ngôi sao',      '👑', 'Năm mươi sao, tuyệt vời!',    'STARS', 50,   4),
    ('first-game',   'Chơi lần đầu',      '🎮', 'Bé đã chơi game đầu tiên!',   'GAMES',  1,   5),
    ('games-10',     'Mê trò chơi',       '🕹️', 'Chơi 10 ván rồi cơ đấy!',     'GAMES', 10,   6),
    ('first-word',   'Tập nói',           '🎤', 'Bé luyện nói lần đầu, hay lắm!', 'WORDS', 1,  7),
    ('words-20',     'Nói giỏi',          '🗣️', 'Luyện 20 từ, bé nói giỏi ghê!', 'WORDS', 20, 8),
    ('streak-3',     'Ba ngày chăm chỉ',  '🔥', 'Ba ngày liền, chăm quá!',     'STREAK', 3,   9),
    ('streak-7',     'Tuần lễ siêng năng', '🏆', 'Cả tuần đều học, xuất sắc!',  'STREAK', 7,  10),
]


def seed(apps, schema_editor):
    Badge = apps.get_model('progress', 'Badge')
    for code, name, icon, desc, kind, threshold, order in BADGES:
        Badge.objects.update_or_create(
            code=code,
            defaults={'name_vi': name, 'icon': icon, 'desc_vi': desc,
                      'kind': kind, 'threshold': threshold, 'order': order, 'active': 'Y'},
        )


def unseed(apps, schema_editor):
    Badge = apps.get_model('progress', 'Badge')
    Badge.objects.filter(code__in=[b[0] for b in BADGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('progress', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
