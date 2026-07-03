"""
Sinh & cung cấp GIỌNG ĐỘNG VIÊN tiếng Việt cho khu của bé (game/phát âm).

Vì sao có file này: giọng `speechSynthesis` của trình duyệt (giọng OS) đọc tiếng
Việt rất tệ (rè, méo). Thay vào đó ta dùng chính `edge-tts` (giọng Neural tự
nhiên) đã có trong dự án để sinh sẵn các câu động viên thành mp3 và CACHE — chạy
một lần lúc setup, sau đó phát offline như audio từ vựng.

Danh sách câu là DỮ LIỆU (PRAISE_LINES) — thêm câu chỉ cần thêm vào đây rồi chạy
lại `manage.py gen_praise`. Client lấy manifest qua API để biết file nào có.
"""

import hashlib
import logging
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage

from . import tts


def _media_root():
    """MEDIA_ROOT dưới dạng Path (override trong test có thể là str)."""
    return Path(settings.MEDIA_ROOT)

logger = logging.getLogger('eng.praise')

# Số lần thử lại edge-tts mỗi câu (server đôi lúc trả NoAudioReceived).
EDGE_RETRIES = 4

# Thư mục cache tương đối trong MEDIA_ROOT.
PRAISE_DIR = 'praise'

# Các câu động viên, gom theo tình huống. Thêm/bớt câu ở đây (dữ liệu, không sửa code).
PRAISE_LINES = {
    'correct': [
        'Giỏi quá!',
        'Tuyệt vời!',
        'Chính xác rồi!',
        'Con làm hay lắm!',
        'Xuất sắc!',
        'Đúng rồi, giỏi ghê!',
    ],
    'wrong': [
        'Không sao đâu, thử lại nhé!',
        'Gần đúng rồi, cố lên nào!',
        'Nghe lại một lần nữa nhé!',
    ],
    'cheer': [
        'Hoan hô, con giỏi lắm!',
        'Tuyệt vời ông mặt trời!',
        'Con làm được rồi, giỏi quá!',
    ],
}


def _default_voice():
    return getattr(settings, 'TTS_VOICE_VI', 'vi-VN-HoaiMyNeural')


def _slug(text, voice):
    """
    Tên file ổn định theo (nội dung câu + giọng) → sinh lại không tạo trùng, và
    CÙNG câu đọc bằng giọng khác nhau ra file khác nhau (vd lời khen huy hiệu
    dùng giọng nam, không đè lên giọng động viên nữ).
    """
    return hashlib.md5(f'{voice}|{text}'.encode('utf-8')).hexdigest()[:12]


def filename_for(text, voice=None):
    """Đường dẫn tương đối (so với MEDIA_ROOT) của file mp3 cho một câu + giọng."""
    return f'{PRAISE_DIR}/{_slug(text, voice or _default_voice())}.mp3'


def _edge_only(text, out_path, voice):
    """
    Sinh mp3 CHỈ bằng edge-tts (giọng Neural), thử lại vài lần. Trả True nếu được.

    Vì sao không dùng tts.synthesize_to_file: hàm đó tự rơi về pyttsx3 (giọng OS)
    khi edge-tts lỗi — mà giọng OS chính là thứ ta muốn tránh cho lời động viên.
    Ở đây thà để trống (client bỏ qua giọng) còn hơn dùng giọng robot.
    """
    for attempt in range(1, EDGE_RETRIES + 1):
        try:
            tts._edge_tts_save(text, out_path, voice)
            return True
        except Exception:
            logger.warning('edge-tts lỗi (lần %d/%d) cho %r', attempt, EDGE_RETRIES, text)
    logger.error('Bỏ qua giọng động viên (edge-tts thất bại): %r', text)
    return False


def generate_line(text, voice, force=False):
    """
    Sinh mp3 cho MỘT câu bằng `voice` (nếu chưa có). Trả 'gen'/'skip'/'fail'.

    Dùng chung cho lời động viên (giọng nữ) và lời khen huy hiệu (giọng nam) —
    không lặp logic. Idempotent theo (câu+giọng).
    """
    if not text:
        return 'skip'
    out_path = _media_root() / filename_for(text, voice)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not force:
        return 'skip'
    return 'gen' if _edge_only(text, out_path, voice) else 'fail'


def _badge_lines():
    """Các lời khen huy hiệu (desc_vi) đang dùng — lấy từ DB, bỏ trùng/rỗng."""
    # Import trong hàm để tránh vòng import (progress phụ thuộc catalog nhẹ).
    from progress.models import Badge
    seen, out = set(), []
    for desc in Badge.objects.filter(active='Y').values_list('desc_vi', flat=True):
        if desc and desc not in seen:
            seen.add(desc)
            out.append(desc)
    return out


def generate_all(force=False):
    """
    Sinh mp3 cho MỌI câu động viên (giọng nữ) + lời khen huy hiệu (giọng nam).
    Trả (đã_sinh, bỏ_qua, lỗi). Dùng bởi lệnh `gen_praise`. CHỈ edge-tts (retry).
    """
    voice = _default_voice()
    badge_voice = getattr(settings, 'TTS_VOICE_BADGE', 'vi-VN-NamMinhNeural')

    generated = skipped = failed = 0
    # Lời động viên game — giọng nữ.
    for lines in PRAISE_LINES.values():
        for text in lines:
            r = generate_line(text, voice, force)
            generated += r == 'gen'; skipped += r == 'skip'; failed += r == 'fail'
    # Lời khen huy hiệu — giọng nam (khác giọng động viên để bé thấy đặc biệt).
    for text in _badge_lines():
        r = generate_line(text, badge_voice, force)
        generated += r == 'gen'; skipped += r == 'skip'; failed += r == 'fail'
    return generated, skipped, failed


def _url_if_exists(text, voice):
    """URL mp3 của (câu+giọng) nếu đã sinh, ngược lại ''."""
    rel = filename_for(text, voice)
    # default_storage.url → có '/' đầu đúng (như FileField.url của audio từ).
    return default_storage.url(rel) if (_media_root() / rel).exists() else ''


def manifest():
    """
    Trả manifest lời động viên game (giọng nữ): {tình_huống: [url_mp3_đã_có, ...]}.
    Rỗng → client bỏ qua giọng, vẫn có confetti + âm thanh.
    """
    voice = _default_voice()
    data = {}
    for key, lines in PRAISE_LINES.items():
        data[key] = [u for u in (_url_if_exists(t, voice) for t in lines) if u]
    return data


def badge_voice_url(desc_vi):
    """URL mp3 giọng NAM đọc lời khen huy hiệu `desc_vi` (đã sinh), hoặc '' nếu chưa."""
    badge_voice = getattr(settings, 'TTS_VOICE_BADGE', 'vi-VN-NamMinhNeural')
    return _url_if_exists(desc_vi, badge_voice)
