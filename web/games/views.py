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
from catalog.models import Topic
from core.models import YesNo
from .engine.registry import load_game_module
from .models import GameResult, GameType

logger = logging.getLogger('eng.games')


@login_required
def choose(request):
    """Chọn bé + chủ đề + loại game."""
    children = ChildProfile.objects.filter(owner=request.user, active='Y')
    topics = Topic.objects.filter(active='Y')
    games = GameType.objects.filter(active='Y')
    return render(request, 'games/choose.html',
                  {'children': children, 'topics': topics, 'games': games})


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
    return JsonResponse({'ok': True, **result})
