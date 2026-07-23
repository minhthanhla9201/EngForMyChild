"""Gán description + level cho các mốc linh vật đã có (seed data bổ sung)."""

from django.db import migrations


def seed(apps, schema_editor):
    PetStage = apps.get_model('progress', 'PetStage')
    data = [
        (0,   'Khởi đầu hành trình',     1),
        (50,  'Em đang lớn dần',         2),
        (100,  'Vững vàng từng bước',     3),
        (200,  'Bản lĩnh hơn mỗi ngày',   4),
        (350, 'Tự tin giao tiếp',        5),
        (500, 'Tỏa sáng rực rỡ',        6),
    ]
    for threshold, desc, level in data:
        PetStage.objects.filter(threshold=threshold).update(
            description=desc, level=level)


def unseed(apps, schema_editor):
    PetStage = apps.get_model('progress', 'PetStage')
    PetStage.objects.all().update(description='', level=1)


class Migration(migrations.Migration):

    dependencies = [
        ('progress', '0008_petstage_description_petstage_level'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
