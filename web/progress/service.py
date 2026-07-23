"""
Tính tiến độ của một bé và mở khoá huy hiệu — logic dùng chung (trang chủ khu bé,
màn kết thúc game/luyện). Tách riêng khỏi view để dễ test.

Chỉ số tiến độ TÍNH từ dữ liệu đã có (GameResult, Attempt) — không lưu trùng:
- total_stars      : sao game + sao phát âm (mastery-based).
- games_played     : số ván game đã chơi.
- game_stars       : sao từ game (Sum GameResult.stars).
- speech_stars     : sao từ phát âm (thành thạo*3 + đang học*1).
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
_DEFAULT_STAGE = (0, '🌱', 'Hạt mầm', '', 1)


def _pet_stages():
    """Danh sách mốc linh vật đang dùng, tăng dần theo ngưỡng sao (đọc từ DB)."""
    return list(PetStage.objects.filter(active='Y').order_by('threshold'))


def _counts(child):
    """Đếm các chỉ số thô của bé. Trả dict. Kết quả được gọi nhiều lần (summary + badges)."""
    from catalog.models import Word

    game_stars = GameResult.objects.filter(child=child).aggregate(s=Sum('stars'))['s'] or 0
    games = GameResult.objects.filter(child=child).count()
    words = Attempt.objects.filter(child=child).count()

    # Sao phát âm dựa trên mastery: chống farm (mỗi từ đóng góp 1 lần).
    attempted_words = Word.objects.filter(attempts__child=child).distinct()
    wm = word_mastery_data(child, attempted_words) if attempted_words else {}
    mastered = sum(1 for m in wm.values() if m['level'] == 'mastered')
    familiar = sum(1 for m in wm.values() if m['level'] == 'familiar')
    learning = sum(1 for m in wm.values() if m['level'] == 'learning')
    speech_stars = mastered * 3 + familiar * 2 + learning * 1

    return {
        'game_stars': game_stars,
        'speech_stars': speech_stars,
        'mastered': mastered,
        'familiar': familiar,
        'learning': learning,
        'total_stars': game_stars + speech_stars,
        'games': games,
        'words': words,
    }


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
    khi bảng rỗng) để lấy icon_src, description, level. `stages` truyền vào để
    tránh truy vấn lặp.
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
    c = _counts(child)
    streak = _streak_days(child)
    metric = {
        Badge.Kind.TOTAL_STARS: c['total_stars'],
        Badge.Kind.GAMES_PLAYED: c['games'],
        Badge.Kind.WORDS_PRACTICED: c['words'],
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
    c = _counts(child)
    total_stars = c['total_stars']
    streak = _streak_days(child)
    stages = _pet_stages()
    level, emoji, name, stage = pet_stage(total_stars, stages)
    remain, next_need = _next_pet_target(total_stars, stages)
    # % tiến tới mốc kế: từ ngưỡng mốc HIỆN TẠI đến ngưỡng mốc KẾ (để thanh đầy dần).
    if next_need:
        cur_need = stages[level].threshold if stages else 0
        span = next_need - cur_need
        pet_percent = int((total_stars - cur_need) / span * 100) if span > 0 else 0
    else:
        pet_percent = 100  # đã tối đa
    # icon_src: URL <img> của linh vật (ảnh upload/SVG offline); rỗng → fallback emoji text.
    pet_icon_src = stage.icon_src if stage else ''

    # Mốc kế tiếp (để hiển thị "còn X sao để thành Y").
    if stages and level + 1 < len(stages):
        next_stage = stages[level + 1]
        pet_next_emoji = next_stage.emoji
        pet_next_name = next_stage.name_vi
        pet_next_icon_src = next_stage.icon_src
    else:
        pet_next_emoji = ''
        pet_next_name = ''
        pet_next_icon_src = ''

    earned = list(ChildBadge.objects.filter(child=child).select_related('badge')
                  .order_by('badge__order', 'badge__threshold'))
    earned_ids = {cb.badge_id for cb in earned}
    all_badges = list(Badge.objects.filter(active='Y'))

    return {
        'total_stars': total_stars,
        'game_stars': c['game_stars'],
        'speech_stars': c['speech_stars'],
        'mastered_words': c['mastered'],
        'familiar_words': c['familiar'],
        'learning_words': c['learning'],
        'games_played': c['games'],
        'words_practiced': c['words'],
        'streak_days': streak,
        'pet_level': level,
        'pet_emoji': emoji,            # fallback text nếu không có SVG/ảnh
        'pet_icon_src': pet_icon_src,  # URL icon để render <img> (ưu tiên)
        'pet_name': name,
        'pet_description': stage.description if stage else _DEFAULT_STAGE[3],
        'pet_level_num': stage.level if stage else _DEFAULT_STAGE[4],
        'pet_remain_stars': remain,      # còn thiếu bao nhiêu sao để lên mốc kế
        'pet_next_need': next_need,
        'pet_percent': pet_percent,      # % đầy thanh tiến tới mốc kế
        'pet_next_emoji': pet_next_emoji,  # emoji mốc kế (dùng cho khích lệ)
        'pet_next_name': pet_next_name,    # tên mốc kế
        'pet_next_icon_src': pet_next_icon_src,  # icon mốc kế (SVG/ảnh)

        # Huy hiệu: đã mở + tổng số (để hiện "3/8" và các ô khoá).
        'badges_earned': [cb.badge for cb in earned],
        'badges_total': len(all_badges),
        'badges_all': [{'badge': b, 'earned': b.id in earned_ids} for b in all_badges],
    }


# ==============================================================================
# ĐỘ THÀNH THẠO CHO TỪNG TỪ (per-word mastery)
# ==============================================================================

# Ngưỡng: trung bình 3 lần gần nhất.
WORD_FAMILIAR_THRESHOLD = 40  # >= 40% → gần thuộc (2⭐)
WORD_MASTERY_THRESHOLD = 60   # >= 60% → thành thạo (3⭐)


def word_mastery_data(child, words):
    """
    Tính độ thành thạo cho từng từ dựa trên lịch sử luyện phát âm (Attempt).

    `words` là iterable các Word objects. Trả về dict:
        {word_id: {
            'level': 'new' | 'learning' | 'familiar' | 'mastered',
            'level_label': 'Chưa học' | 'Đang học' | 'Gần đạt' | 'Thành thạo',
            'icon': 'new' | 'book' | 'thumbs' | 'star',
            'avg_score': int (0-100),
            'attempts': int,
            'scores': list[int] (tối đa 3 lần gần nhất),
        }}

    Thuật toán:
      - 3 lần gần nhất (có score), trung bình >= WORD_MASTERY_THRESHOLD
        VÀ có ít nhất 2 lần attempt → 'mastered' (3⭐)
      - Trung bình >= WORD_FAMILIAR_THRESHOLD VÀ có ít nhất 2 lần attempt
        → 'familiar' (2⭐)
      - Đã có attempt → 'learning' (1⭐)
      - Chưa có attempt nào → 'new' (0⭐)
    """
    from pronunciation.models import Attempt

    # Query tất cả attempt có score (đã được chấm ASR).
    attempts = (Attempt.objects
                .filter(child=child, word__in=words, score__isnull=False)
                .order_by('word_id', '-created_at'))

    # Gom theo word_id, lấy tối đa 3 score gần nhất.
    tmp = {}
    for a in attempts:
        if a.word_id not in tmp:
            tmp[a.word_id] = {'attempts': 0, 'scores': []}
        entry = tmp[a.word_id]
        if entry['attempts'] < 3:
            entry['scores'].append(a.score)
        entry['attempts'] += 1

    # Xây dict kết quả, gán level cho từng word.
    mastery = {}
    for wid, entry in tmp.items():
        scores = entry['scores']
        avg = sum(scores) / len(scores) if scores else 0
        if entry['attempts'] >= 2 and avg >= WORD_MASTERY_THRESHOLD:
            level, label, icon = 'mastered', 'Thành thạo', 'star'
        elif entry['attempts'] >= 2 and avg >= WORD_FAMILIAR_THRESHOLD:
            level, label, icon = 'familiar', 'Gần đạt', 'thumbs'
        else:
            level, label, icon = 'learning', 'Đang học', 'book'
        mastery[wid] = {
            'level': level,
            'level_label': label,
            'icon': icon,
            'avg_score': int(avg),
            'attempts': entry['attempts'],
            'scores': scores,
        }

    # Word chưa có attempt nào → 'new'.
    for w in words:
        if w.id not in mastery:
            mastery[w.id] = {
                'level': 'new',
                'level_label': 'Chưa học',
                'icon': 'new',
                'avg_score': 0,
                'attempts': 0,
                'scores': [],
            }

    return mastery


def topic_mastery_data(child, topics):
    """
    Tính tiến độ cho từng chủ đề dựa trên độ thành thạo của các từ trong chủ đề.

    `topics` là iterable các Topic objects. Trả về dict:
        {topic_id: {
            'total_words': int,
            'practiced_words': int,   # learning + mastered
            'pct': int,               # 0-100
        }}
    """
    from catalog.models import Word

    # Lấy tất cả từ active trong các chủ đề.
    words = Word.objects.filter(topic__in=topics, active='Y').select_related('topic')
    wm = word_mastery_data(child, words)

    # Gom theo topic.
    tmp = {}
    for w in words:
        if w.topic_id not in tmp:
            tmp[w.topic_id] = {'total': 0, 'practiced': 0}
        tmp[w.topic_id]['total'] += 1
        if wm.get(w.id, {}).get('level') in ('learning', 'familiar', 'mastered'):
            tmp[w.topic_id]['practiced'] += 1

    result = {}
    for tid, entry in tmp.items():
        pct = int(entry['practiced'] / entry['total'] * 100) if entry['total'] > 0 else 0
        result[tid] = {
            'total_words': entry['total'],
            'practiced_words': entry['practiced'],
            'pct': pct,
        }
    return result


def game_word_progress_data(child, topics):
    """
    Tính tiến độ game cho từng chủ đề dựa trên word_results từ GameResult.

    Không dùng Attempt (pronunciation) — mỗi GameResult có word_results
    (JSONField) ghi lại word_id + correct/sai cho từng từ trong ván chơi.

    Trả về dict:
        {topic_id: {
            'total_words': int,
            'played_words': int,   # từ đã trả lời ĐÚNG trong ít nhất 1 ván game
            'pct': int,
        }}
    """
    from catalog.models import Word

    # Đếm tổng số từ active trong mỗi chủ đề.
    words = Word.objects.filter(topic__in=topics, active='Y').select_related('topic')
    total_by_topic = {}
    for w in words:
        total_by_topic[w.topic_id] = total_by_topic.get(w.topic_id, 0) + 1

    # Lấy word_results từ GameResult, lọc rỗng trong Python.
    qs = GameResult.objects.filter(child=child, topic__in=topics).values_list('topic_id', 'word_results')

    # Tập hợp word_id đã trả lời ĐÚNG trong game, theo topic.
    played_by_topic = {}
    for tid, wr_list in qs:
        if not wr_list:
            continue
        if tid not in played_by_topic:
            played_by_topic[tid] = set()
        for wr in wr_list:
            wid = wr.get('word_id') if isinstance(wr, dict) else None
            if wid and wr.get('correct'):         # chỉ tính khi trả lời đúng
                played_by_topic[tid].add(wid)

    result = {}
    for tid in total_by_topic:
        total = total_by_topic[tid]
        played = len(played_by_topic.get(tid, set()))
        pct = int(played / total * 100) if total > 0 else 0
        result[tid] = {
            'total_words': total,
            'played_words': played,
            'pct': pct,
        }
    return result
