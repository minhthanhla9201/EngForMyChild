"""Thêm huy hiệu cấp cao (ngưỡng lớn hơn) — cho bé đã đạt hết huy hiệu cũ."""

from django.db import migrations

# (code, tên, icon, lời khen, loại điều kiện, ngưỡng, thứ tự)
# Loại: STARS=tổng sao · GAMES=lượt chơi · WORDS=lần luyện · STREAK=chuỗi ngày.
BADGES = [
    # === SAO — cấp cao (cấp cũ max 50) ===
    ('stars-100',    'Ngôi sao lấp lánh',     '🌟', '100 sao rực rỡ, em giỏi quá!',              'STARS',  100,  11),
    ('stars-250',    'Mặt trăng sao',         '🌙', '250 sao sáng như trăng rằm!',                'STARS',  250,  12),
    ('stars-500',    'Mặt trời rực rỡ',       '☀️', '500 sao chói lọi như mặt trời!',             'STARS',  500,  13),
    ('stars-1000',   'Dải ngân hà',           '🌌', '1000 sao em tạo nên cả dải ngân hà!',        'STARS', 1000,  14),
    ('stars-2000',   'Sao băng',              '🌠', '2000 sao — vút bay như sao băng!',           'STARS', 2000,  15),

    # === GAME — cấp cao (cấp cũ max 10) ===
    ('games-30',     'Rạp xiếc',              '🎪', '30 ván rộn ràng như rạp xiếc!',              'GAMES',   30,  16),
    ('games-60',     'Bắn trúng',             '🎯', '60 ván — bắn trúng mục tiêu rồi!',            'GAMES',   60,  17),
    ('games-100',    'Sân vận động',          '🏟', '100 ván — em chơi hết mình như trên sân!',    'GAMES',  100,  18),
    ('games-200',    'Cúp vô địch',           '🏆', '200 ván — em là nhà vô địch!',                'GAMES',  200,  19),

    # === LUYỆN NÓI — cấp cao (cấp cũ max 20) ===
    ('words-50',     'Tủ sách',               '📚', '50 từ luyện nói — đầy một tủ sách!',          'WORDS',   50,  20),
    ('words-100',    'Tốt nghiệp',            '🎓', '100 từ — em tốt nghiệp khoá phát âm!',         'WORDS',  100,  21),
    ('words-200',    'Từ điển sống',          '📖', '200 từ — em là từ điển sống!',                'WORDS',  200,  22),
    ('words-500',    'Bách khoa toàn thư',    '🧠', '500 từ — em là bách khoa toàn thư!',          'WORDS',  500,  23),

    # === CHUỖI NGÀY — cấp cao (cấp cũ max 7) ===
    ('streak-14',    'Mầm xanh',              '🌿', '14 ngày liên tiếp — mầm xanh đã nảy!',        'STREAK',  14,  24),
    ('streak-30',    'Hoa mặt trời',          '🌻', '30 ngày liên tiếp — nở hoa rực rỡ!',          'STREAK',  30,  25),
    ('streak-60',    'Cây đại thụ',           '🌳', '60 ngày liên tiếp — vững như cây đại thụ!',   'STREAK',  60,  26),
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
        ('progress', '0006_assign_icon_static'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
