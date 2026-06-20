"""
Sinh audio TTS cho một từ, lưu ra file mp3.

Chiến lược (theo lựa chọn "cả hai, tự dự phòng"):
  1) edge-tts (giọng Microsoft Neural, hay hơn) — CẦN internet.
  2) Nếu lỗi/không có mạng → pyttsx3 (đọc bằng giọng hệ điều hành) — KHÔNG cần mạng.

Tách riêng để mock trong test (không gọi mạng/đọc loa thật).
"""

import asyncio
import logging

from django.conf import settings

logger = logging.getLogger('eng.tts')


def synthesize_to_file(text_en, out_path, voice=None):
    """
    Sinh audio cho `text_en` ra `out_path` (mp3/wav).

    Trả về tên provider đã dùng ('edge-tts' / 'pyttsx3'), hoặc None nếu cả hai thất bại.
    KHÔNG raise — bên gọi tự xử lý khi trả None.
    """
    voice = voice or getattr(settings, 'TTS_VOICE', 'en-US-AnaNeural')

    # 1) Ưu tiên edge-tts (cần mạng).
    try:
        _edge_tts_save(text_en, out_path, voice)
        logger.info('Đã sinh audio bằng edge-tts: %s', text_en)
        return 'edge-tts'
    except Exception:
        # Mạng chập chờn / không có mạng → ghi cảnh báo, chuyển dự phòng.
        logger.warning('edge-tts thất bại cho %r, chuyển sang pyttsx3.', text_en, exc_info=True)

    # 2) Dự phòng pyttsx3 (offline).
    try:
        _pyttsx3_save(text_en, out_path)
        logger.info('Đã sinh audio bằng pyttsx3 (offline): %s', text_en)
        return 'pyttsx3'
    except Exception:
        logger.exception('pyttsx3 cũng thất bại cho %r', text_en)
        return None


def _edge_tts_save(text_en, out_path, voice):
    """Gọi edge-tts (bất đồng bộ) để lưu mp3. Raise nếu lỗi/không mạng."""
    import edge_tts

    async def _run():
        communicate = edge_tts.Communicate(text_en, voice)
        await communicate.save(str(out_path))

    asyncio.run(_run())


def _pyttsx3_save(text_en, out_path):
    """Dùng pyttsx3 đọc và lưu file (offline). Raise nếu lỗi."""
    import pyttsx3

    engine = pyttsx3.init()
    engine.save_to_file(text_en, str(out_path))
    engine.runAndWait()
