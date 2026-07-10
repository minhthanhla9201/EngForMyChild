"""
Điều phối audio phát âm cho từ — API dùng chung cho view/template/lệnh import.

get_clip(word): ưu tiên clip đã có (recorded/default); nếu chưa có thì sinh TTS,
LƯU lại (cache) rồi trả về. Lần sau dùng file đã có → không gọi TTS lại.
KHÔNG gọi edge-tts/pyttsx3 trực tiếp ở nơi khác — luôn qua đây.
"""

import logging

from django.conf import settings

from core.models import YesNo
from .models import AudioClip
from . import tts

logger = logging.getLogger('eng.audio')


def get_existing_clip(word):
    """Trả clip ưu tiên đã có của từ (recorded/default trước), hoặc None."""
    # ordering của model: -is_default → clip mặc định lên đầu. Ưu tiên recorded.
    return (word.clips.order_by('-is_default')
            .filter(source=AudioClip.Source.RECORDED).first()
            or word.clips.order_by('-is_default').first())


def get_clip(word, force=False):
    """
    Lấy AudioClip phát âm cho `word`. Nếu chưa có (hoặc force) thì sinh TTS + cache.

    Trả về AudioClip, hoặc None nếu không sinh được (vd cả 2 provider lỗi).
    """
    if not force:
        existing = get_existing_clip(word)
        if existing:
            return existing

    return generate_tts_clip(word)


def generate_tts_clip(word):
    """Sinh audio TTS cho từ, lưu file vào media/audio/ và tạo AudioClip. Trả clip hoặc None."""
    # Tên file ổn định theo id từ → tránh sinh trùng, dễ tra.
    filename = f'word_{word.pk}.mp3'
    out_path = settings.MEDIA_ROOT / 'audio' / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)

    voice = getattr(settings, 'TTS_VOICE', '')
    provider = tts.synthesize_to_file(word.text_en, out_path, voice=voice)
    if provider is None:
        logger.error('Không sinh được audio cho từ %r (id=%s)', word.text_en, word.pk)
        return None

    # Lưu đường dẫn tương đối so với MEDIA_ROOT vào FileField.
    clip = AudioClip.objects.create(
        word=word,
        source=AudioClip.Source.TTS,
        voice=voice if provider == 'edge-tts' else 'pyttsx3',
        file=f'audio/{filename}',
        is_default=YesNo.YES,
    )
    return clip


def get_vi_instruction(word):
    """
    Sinh & cache audio câu hướng dẫn tiếng Việt: 'X tiếng Anh đọc là Y'.
    Trả URL hoặc None nếu lỗi (vd mất mạng).
    """
    instruction = f"{word.text_vi} .. tiếng Anh em đọc là ..."
    voice = getattr(settings, 'TTS_VOICE_VI', 'vi-VN-HoaiMyNeural')

    filename = f'inst_{word.pk}.mp3'
    out_path = settings.MEDIA_ROOT / 'instructions' / filename

    if not out_path.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            tts._edge_tts_save(instruction, out_path, voice)
        except Exception:
            logger.warning('Không sinh được hướng dẫn cho từ %r', word.text_en)
            return None

    from django.core.files.storage import default_storage
    return default_storage.url(f'instructions/{filename}')


def get_vi_name(word):
    """
    Sinh & cache audio đọc CHỈ TÊN TIẾNG VIỆT của từ (vd 'con mèo') — dùng cho game
    có hình: bé chưa biết chữ, chạm vào hình sẽ nghe tên hình bằng giọng.

    Khác get_vi_instruction (đọc câu dài): đây chỉ đọc text_vi ngắn gọn. Cache
    media/names/name_<pk>.mp3, giọng nữ TTS_VOICE_VI. Trả URL hoặc None nếu lỗi/offline.
    Idempotent: đã có file thì trả luôn (không gọi TTS lại).
    """
    if not word.text_vi:
        return None
    voice = getattr(settings, 'TTS_VOICE_VI', 'vi-VN-HoaiMyNeural')

    filename = f'name_{word.pk}.mp3'
    # Path() để hoạt động cả khi MEDIA_ROOT là str (vd test override_settings).
    from pathlib import Path
    out_path = Path(settings.MEDIA_ROOT) / 'names' / filename

    if not out_path.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            tts._edge_tts_save(word.text_vi, out_path, voice)
        except Exception:
            logger.warning('Không sinh được tên tiếng Việt cho từ %r', word.text_en)
            return None

    from django.core.files.storage import default_storage
    return default_storage.url(f'names/{filename}')
