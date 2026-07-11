"""
Tính tiến độ của một bé và mở khoá huy hiệu — logic dùng chung (trang chủ khu bé,
màn kết thúc game/luyện). Tách riêng khỏi view để dễ test.

Chỉ số tiến độ TÍNH từ dữ liệu đã có (GameResult, Attempt) — không lưu trùng:
- total_stars      : tổng sao tích luỹ từ game.
- games_played     : số ván game đã chơi.
- words_practiced  : số lần luyện phát âm.
- streak_days      : số ngày học/chơi LIÊN TIẾP tính đến hôm nay.
- pet_level/pet_emoji : "linh vật lớn dần" theo tổng sao (hạt → cây → …).
"""

from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from games.models import GameResult
from pronunciation.models import Attempt
from .models import Badge, ChildBadge, PetStage

# Mốc mặc định khi bảng PetStage RỖNG (chưa seed) — để trang không vỡ.
# Bình thường các mốc lấy từ DB (PetStage) để phụ huynh tự chỉnh qua trang quản lý.
_DEFAULT_STAGE = (0, '🌱', 'Hạt mầm')


def _pet_stages():
    """Danh sách mốc linh vật đang dùng, tăng dần theo ngưỡng sao (đọc từ DB)."""
    return list(PetStage.objects.filter(active='Y').order_by('threshold'))


def _counts(child):
    """Đếm các chỉ số thô của bé (1 lượt truy vấn mỗi loại)."""
    stars = GameResult.objects.filter(child=child).aggregate(s=Sum('stars'))['s'] or 0
    games = GameResult.objects.filter(child=child).count()
    words = Attempt.objects.filter(child=child).count()
    return stars, games, words


def _streak_days(child):
    """
    Số ngày LIÊN TIẾP (tính đến hôm nay) bé có hoạt động (chơi game hoặc luyện).

    Gộp ngày từ cả GameResult và Attempt; đếm lùi từ hôm nay đến khi gặp ngày trống.
    Nếu hôm nay chưa hoạt động nhưng hôm qua có, chuỗi vẫn tính tới hôm qua.
    """
    # Lấy tập các ngày (local) có hoạt động.
    days = set()
    for qs in (GameResult.objects.filter(child=child), Attempt.objects.filter(child=child)):
        for created in qs.values_list('created_at', flat=True):
            days.add(timezone.localtime(created).date())
    if not days:
        return 0

    today = timezone.localdate()
    # Mốc bắt đầu: hôm nay nếu có hoạt động, ngược lại hôm qua (không làm đứt oan).
    start = today if today in days else today - timedelta(days=1)
    streak = 0
    d = start
    while d in days:
        streak += 1
        d -= timedelta(days=1)
    return streak


def pet_stage(total_stars, stages=None):
    """
    Trả (level_index, emoji, name_vi, stage) của linh vật theo tổng sao.

    Chọn mốc CAO NHẤT mà tổng sao đạt. `stage` là đối tượng PetStage (hoặc None
    khi bảng rỗng) để lấy icon_src. `stages` truyền vào để tránh truy vấn lặp.
    """
    if stages is None:
        stages = _pet_stages()
    if not stages:
        # Bảng chưa seed → mốc mặc định, không có object (icon fallback emoji text).
        return 0, _DEFAULT_STAGE[1], _DEFAULT_STAGE[2], None
    idx, chosen = 0, stages[0]
    for i, st in enumerate(stages):
        if total_stars >= st.threshold:
            idx, chosen = i, st
    return idx, chosen.emoji, chosen.name_vi, chosen


def _next_pet_target(total_stars, stages=None):
    """Số sao còn thiếu để lên mốc linh vật kế tiếp (None nếu đã tối đa)."""
    if stages is None:
        stages = _pet_stages()
    for st in stages:
        if total_stars < st.threshold:
            return st.threshold - total_stars, st.threshold
    return None, None


def check_and_award_badges(child):
    """
    Mở khoá các huy hiệu bé VỪA đủ điều kiện (chưa có). Trả list Badge mới mở.

    Idempotent: huy hiệu đã có thì bỏ qua (UniqueConstraint chặn trùng). Gọi sau
    mỗi ván chơi / lần luyện để trao kịp thời.
    """
    stars, games, words = _counts(child)
    streak = _streak_days(child)
    metric = {
        Badge.Kind.TOTAL_STARS: stars,
        Badge.Kind.GAMES_PLAYED: games,
        Badge.Kind.WORDS_PRACTICED: words,
        Badge.Kind.STREAK_DAYS: streak,
    }

    have = set(ChildBadge.objects.filter(child=child).values_list('badge_id', flat=True))
    newly = []
    for badge in Badge.objects.filter(active='Y'):
        if badge.id in have:
            continue
        if metric.get(badge.kind, 0) >= badge.threshold:
            # get_or_create: an toàn nếu chạy song song (UniqueConstraint bảo vệ).
            _obj, created = ChildBadge.objects.get_or_create(child=child, badge=badge)
            if created:
                newly.append(badge)
    return newly


def summary(child):
    """
    Toàn bộ tiến độ của bé để hiển thị (trang chủ/màn kết thúc). Không mở khoá gì
    thêm — chỉ đọc. Trả dict thuần (dễ đưa vào template / json_script).
    """
    stars, games, words = _counts(child)
    streak = _streak_days(child)
    stages = _pet_stages()
    level, emoji, name, stage = pet_stage(stars, stages)
    remain, next_need = _next_pet_target(stars, stages)
    # % tiến tới mốc kế: từ ngưỡng mốc HIỆN TẠI đến ngưỡng mốc KẾ (để thanh đầy dần).
    if next_need:
        cur_need = stages[level].threshold if stages else 0
        span = next_need - cur_need
        pet_percent = int((stars - cur_need) / span * 100) if span > 0 else 0
    else:
        pet_percent = 100  # đã tối đa
    # icon_src: URL <img> của linh vật (ảnh upload/SVG offline); rỗng → fallback emoji text.
    pet_icon_src = stage.icon_src if stage else ''

    earned = list(ChildBadge.objects.filter(child=child).select_related('badge')
                  .order_by('badge__order', 'badge__threshold'))
    earned_ids = {cb.badge_id for cb in earned}
    all_badges = list(Badge.objects.filter(active='Y'))

    return {
        'total_stars': stars,
        'games_played': games,
        'words_practiced': words,
        'streak_days': streak,
        'pet_level': level,
        'pet_emoji': emoji,            # fallback text nếu không có SVG/ảnh
        'pet_icon_src': pet_icon_src,  # URL icon để render <img> (ưu tiên)
        'pet_name': name,
        'pet_remain_stars': remain,      # còn thiếu bao nhiêu sao để lên mốc kế
        'pet_next_need': next_need,
        'pet_percent': pet_percent,      # % đầy thanh tiến tới mốc kế

        # Huy hiệu: đã mở + tổng số (để hiện "3/8" và các ô khoá).
        'badges_earned': [cb.badge for cb in earned],
        'badges_total': len(all_badges),
        'badges_all': [{'badge': b, 'earned': b.id in earned_ids} for b in all_badges],
    }
