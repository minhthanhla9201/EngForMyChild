"""
Gán SVG tĩnh (static/icons/topic/) + emoji hợp nghĩa cho các chủ đề.

VÌ SAO: Topic.icon trước đây là emoji thô → phụ thuộc font máy đích. Chuyển sang
SVG tĩnh commit theo repo (giống Badge/PetStage). Nhiều topic đang để mặc định 📚
→ gán emoji sát nghĩa hơn cho từng chủ đề (part A), topic đã có emoji đúng thì
SVG khớp luôn (part B).

Idempotent: chỉ gán icon_static khi đang trống (không đè lựa chọn thủ công).
emoji chỉ cập nhật khi đang là mặc định '📚' (không đè emoji người dùng đã đổi).
"""

from django.db import migrations

# slug → (đường dẫn static SVG, emoji hợp nghĩa). SVG đã copy vào static/icons/topic/.
TOPIC_ICONS = {
    'actions':     ('icons/topic/actions.svg',     '🏃'),
    'animals':     ('icons/topic/animals.svg',     '🐱'),
    'bathroom':    ('icons/topic/bathroom.svg',    '🛁'),
    'birds':       ('icons/topic/birds.svg',       '🐦'),
    'body':        ('icons/topic/body.svg',        '✋'),
    'clothes':     ('icons/topic/clothes.svg',     '👕'),
    'colors':      ('icons/topic/colors.svg',      '🔴'),
    'drinks':      ('icons/topic/drinks.svg',      '🥤'),
    'family':      ('icons/topic/family.svg',      '👩'),
    'feelings':    ('icons/topic/feelings.svg',    '😊'),
    'food':        ('icons/topic/food.svg',        '🍔'),
    'fruits':      ('icons/topic/fruits.svg',      '🍎'),
    'house':       ('icons/topic/house.svg',       '🏠'),
    'insects':     ('icons/topic/insects.svg',     '🐛'),
    'jobs':        ('icons/topic/jobs.svg',        '👷'),
    'music':       ('icons/topic/music.svg',       '🎵'),
    'nature':      ('icons/topic/nature.svg',      '🌳'),
    'numbers':     ('icons/topic/numbers.svg',     '1️⃣'),
    'reptiles':    ('icons/topic/reptiles.svg',    '🐢'),
    'school':      ('icons/topic/school.svg',      '🎒'),
    'sea-animals': ('icons/topic/sea-animals.svg', '🐟'),
    'shapes':      ('icons/topic/shapes.svg',      '🔷'),
    'sports':      ('icons/topic/sports.svg',      '⚽'),
    'time':        ('icons/topic/time.svg',        '🕐'),
    'toys':        ('icons/topic/toys.svg',        '🧸'),
    'vegetables':  ('icons/topic/vegetables.svg',  '🥕'),
    'vehicles':    ('icons/topic/vehicles.svg',    '🚗'),
    'weather':     ('icons/topic/weather.svg',     '☀️'),
}


def assign(apps, schema_editor):
    Topic = apps.get_model('catalog', 'Topic')
    for slug, (path, emoji) in TOPIC_ICONS.items():
        # Chỉ gán SVG tĩnh khi chưa có (không đè ảnh/lựa chọn thủ công).
        Topic.objects.filter(slug=slug, icon_static='').update(icon_static=path)
        # Nâng emoji fallback cho topic còn để mặc định '📚' (không đè emoji đã đổi).
        Topic.objects.filter(slug=slug, icon='📚').update(icon=emoji)


def unassign(apps, schema_editor):
    Topic = apps.get_model('catalog', 'Topic')
    paths = [p for p, _e in TOPIC_ICONS.values()]
    Topic.objects.filter(icon_static__in=paths).update(icon_static='')


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_topic_icon_image_topic_icon_static_alter_topic_icon'),
    ]

    operations = [
        migrations.RunPython(assign, unassign),
    ]
