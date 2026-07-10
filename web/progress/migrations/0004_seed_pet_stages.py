"""
Seed các mốc linh vật ban đầu (chuyển từ hằng PET_STAGES cũ trong service.py sang DB).

Thêm/đổi mốc = sửa dữ liệu qua trang quản lý hoặc thêm bản ghi tương tự — không sửa code.
Idempotent (update_or_create theo threshold) nên chạy lại an toàn.
"""

from django.db import migrations

# (ngưỡng_sao, emoji, tên_vi, thứ_tự) — xếp tăng dần theo ngưỡng.
PET_STAGES = [
    (0,   '🌱', 'Hạt mầm',      1),
    (10,  '🌿', 'Chồi non',     2),
    (25,  '🪴', 'Cây nhỏ',      3),
    (50,  '🌳', 'Cây lớn',      4),
    (100, '🌸', 'Cây ra hoa',   5),
    (200, '🌟', 'Cây ngôi sao', 6),
]


def seed(apps, schema_editor):
    PetStage = apps.get_model('progress', 'PetStage')
    for threshold, emoji, name, order in PET_STAGES:
        PetStage.objects.update_or_create(
            threshold=threshold,
            defaults={'emoji': emoji, 'name_vi': name, 'order': order, 'active': 'Y'},
        )


def unseed(apps, schema_editor):
    PetStage = apps.get_model('progress', 'PetStage')
    PetStage.objects.filter(threshold__in=[s[0] for s in PET_STAGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('progress', '0003_badge_icon_image_alter_badge_icon_petstage'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
