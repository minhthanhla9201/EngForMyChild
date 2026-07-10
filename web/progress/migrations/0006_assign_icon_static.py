"""
Gán SVG tĩnh (trong static/icons/) cho các linh vật & huy hiệu đã seed.

VÌ SAO: SVG tĩnh commit theo repo → deploy máy khác luôn có icon, không cần tải
mạng (fetch_ui_icons), không phụ thuộc font hệ thống. Đây là nguồn icon MẶC ĐỊNH.

Idempotent: chỉ gán khi icon_static đang trống (không đè lựa chọn thủ công của
phụ huynh). Khớp linh vật theo threshold, huy hiệu theo code.
"""

from django.db import migrations

# threshold → đường dẫn static SVG (file đã copy vào web/static/icons/pet/).
PET_ICONS = {
    0:   'icons/pet/seedling.svg',
    10:  'icons/pet/sprout.svg',
    25:  'icons/pet/potted.svg',
    50:  'icons/pet/tree.svg',
    100: 'icons/pet/blossom.svg',
    200: 'icons/pet/glowing-star.svg',
}

# code → đường dẫn static SVG (file đã copy vào web/static/icons/badge/).
BADGE_ICONS = {
    'first-star': 'icons/badge/first-star.svg',
    'stars-10':   'icons/badge/stars-10.svg',
    'stars-25':   'icons/badge/stars-25.svg',
    'stars-50':   'icons/badge/stars-50.svg',
    'first-game': 'icons/badge/first-game.svg',
    'games-10':   'icons/badge/games-10.svg',
    'first-word': 'icons/badge/first-word.svg',
    'words-20':   'icons/badge/words-20.svg',
    'streak-3':   'icons/badge/streak-3.svg',
    'streak-7':   'icons/badge/streak-7.svg',
}


def assign(apps, schema_editor):
    PetStage = apps.get_model('progress', 'PetStage')
    Badge = apps.get_model('progress', 'Badge')
    for threshold, path in PET_ICONS.items():
        # Chỉ gán khi chưa có (không đè ảnh/icon phụ huynh đã đặt).
        PetStage.objects.filter(threshold=threshold, icon_static='').update(icon_static=path)
    for code, path in BADGE_ICONS.items():
        Badge.objects.filter(code=code, icon_static='').update(icon_static=path)


def unassign(apps, schema_editor):
    PetStage = apps.get_model('progress', 'PetStage')
    Badge = apps.get_model('progress', 'Badge')
    PetStage.objects.filter(icon_static__in=PET_ICONS.values()).update(icon_static='')
    Badge.objects.filter(icon_static__in=BADGE_ICONS.values()).update(icon_static='')


class Migration(migrations.Migration):

    dependencies = [
        ('progress', '0005_badge_icon_static_petstage_icon_static'),
    ]

    operations = [
        migrations.RunPython(assign, unassign),
    ]
