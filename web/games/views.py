"""
View khu trò chơi (kiến trúc khuôn + dữ liệu).

Luồng:
  choose  : chọn bé + chủ đề + loại game.
  play    : nạp module game theo GameType.module, build_round từ kho Word của chủ đề,
            render template riêng của game (play_<module>.html).
  submit  : nhận kết quả client → score_round của module → lưu GameResult → trả sao.
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from accounts.models import ChildProfile
from accounts.utils import get_active_child
from catalog.models import Topic
from core.models import YesNo
from catalog import praise as praise_service
from progress import service as progress_service
from .engine.registry import load_game_module
from .models import GameResult, GameType

logger = logging.getLogger('eng.games')


@login_required
def choose(request):
    """Chọn bé + chủ đề + loại game — chủ đề sắp xếp theo tiến độ của bé."""
    children = ChildProfile.objects.filter(owner=request.user, active='Y')
    topics = Topic.objects.filter(active='Y')
    games = GameType.objects.filter(active='Y')

    child = get_active_child(request)
    topic_list = [(t, None) for t in topics]
    if child:
        td = progress_service.topic_mastery_data(child, topics)
        topic_list = sorted(
            [(t, td.get(t.id)) for t in topics],
            key=lambda x: (x[1] or {}).get('pct', 0),
        )

    return render(request, 'games/choose.html', {
        'children': children,
        'topic_list': topic_list,
        'games': games,
        'hint_voice_url': praise_service.page_hint_url('games_choose'),
    })


@login_required
def play(request, child_id, code, slug):
    """Màn chơi: dựng một vòng từ kho Word của chủ đề rồi render template của game."""
    child = get_object_or_404(ChildProfile, pk=child_id, owner=request.user, active='Y')
    game = get_object_or_404(GameType, code=code, active='Y')
    topic = get_object_or_404(Topic, slug=slug, active='Y')

    # Nếu game cần hình thì chỉ lấy từ có hình; nếu không thì lấy tất cả từ đang dùng.
    words = topic.words.filter(active='Y')
    if game.needs_image == YesNo.YES:
        words = words.exclude(image='')

    if words.count() < game.min_words:
        return render(request, 'games/play_empty.html',
                      {'child': child, 'game': game, 'topic': topic, 'min_words': game.min_words})

    module = load_game_module(game.module)
    round_data = module.build_round(words)

    # Truyền dict thuần; template dùng {{ round_data|json_script }} để serialize an toàn.
    # (KHÔNG json.dumps ở đây — sẽ bị mã hoá 2 lần → client nhận chuỗi thay vì object.)
    return render(request, f'games/play_{game.module}.html', {
        'child': child, 'game': game, 'topic': topic,
        'round_data': round_data,
        # URL mp3 giọng đọc câu hướng dẫn (rỗng nếu chưa sinh → chỉ hiện chữ).
        'hint_voice_url': praise_service.hint_voice_url(game.hint_vi),
    })


@login_required
def submit(request, child_id, code, slug):
    """Nhận kết quả ván chơi (JSON), chấm điểm bằng module, lưu GameResult. Trả sao."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Phương thức không hợp lệ.'}, status=405)

    child = get_object_or_404(ChildProfile, pk=child_id, owner=request.user, active='Y')
    game = get_object_or_404(GameType, code=code, active='Y')
    topic = get_object_or_404(Topic, slug=slug, active='Y')

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'message': 'Dữ liệu không hợp lệ.'}, status=400)

    module = load_game_module(game.module)
    result = module.score_round(payload)

    GameResult.objects.create(
        child=child, game_type=game, topic=topic,
        stars=result.get('stars', 0),
        score=result.get('score', 0),
        total=result.get('total', 0),
        duration_sec=int(payload.get('duration_sec', 0) or 0),
    )
    logger.info('Ván chơi: bé=%s game=%s chủ đề=%s → %s sao', child.name, game.code, topic.slug,
                result.get('stars'))

    # Trao huy hiệu vừa đủ điều kiện → trả về client để hiện "bé vừa đạt".
    # voice_url: mp3 giọng nam (edge-tts) đọc lời khen huy hiệu (rỗng nếu chưa sinh).
    new_badges = progress_service.check_and_award_badges(child)
    result['badges'] = [{'icon': b.icon, 'name_vi': b.name_vi, 'desc_vi': b.desc_vi,
                         'voice_url': praise_service.badge_voice_url(b.desc_vi)}
                        for b in new_badges]
    result['total_stars'] = progress_service.summary(child)['total_stars']
    return JsonResponse({'ok': True, **result})
