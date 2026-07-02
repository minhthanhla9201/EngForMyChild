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


def _slug(text):
    """Tên file ổn định theo nội dung câu (hash ngắn) → sinh lại không tạo trùng."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:12]


def filename_for(text):
    """Đường dẫn tương đối (so với MEDIA_ROOT) của file mp3 cho một câu."""
    return f'{PRAISE_DIR}/{_slug(text)}.mp3'


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


def generate_all(force=False):
    """
    Sinh mp3 cho MỌI câu động viên (nếu chưa có). Trả (đã_sinh, bỏ_qua, lỗi).

    Dùng bởi management command `gen_praise`. Idempotent: file đã có thì bỏ qua
    (trừ khi force). Giọng lấy từ settings.TTS_VOICE_VI. CHỈ dùng edge-tts (có
    retry) — không rơi về giọng OS.
    """
    voice = getattr(settings, 'TTS_VOICE_VI', 'vi-VN-HoaiMyNeural')
    out_dir = _media_root() / PRAISE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    generated = skipped = failed = 0
    for lines in PRAISE_LINES.values():
        for text in lines:
            out_path = _media_root() / filename_for(text)
            if out_path.exists() and not force:
                skipped += 1
                continue
            if _edge_only(text, out_path, voice):
                generated += 1
            else:
                failed += 1
    return generated, skipped, failed


def manifest():
    """
    Trả manifest cho client: {tình_huống: [url_mp3_đã_có, ...]}.

    Chỉ liệt kê file THỰC SỰ tồn tại (đã sinh) → client bốc ngẫu nhiên 1 câu để
    phát; nếu chưa sinh (danh sách rỗng) thì client bỏ qua phần giọng, vẫn có
    confetti + âm thanh.
    """
    data = {}
    for key, lines in PRAISE_LINES.items():
        urls = []
        for text in lines:
            rel = filename_for(text)
            if (_media_root() / rel).exists():
                # default_storage.url → có '/' đầu đúng (như FileField.url của audio từ).
                urls.append(default_storage.url(rel))
        data[key] = urls
    return data
