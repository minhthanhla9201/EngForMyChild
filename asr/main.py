"""
Service chấm phát âm (ASR) — FastAPI + faster-whisper. Chạy RIÊNG trong Docker.

Nhiệm vụ tối giản: nhận file audio bé đọc → trả text nghe được. Việc SO KHỚP với
từ đích và quy ra sao nằm ở web (pronunciation/asr.py) — service này chỉ nhận dạng.

Giọng bé chỉ tới service local này, KHÔNG gửi ra ngoài (whisper chạy offline sau
khi đã tải model về volume). Model + ngôn ngữ cấu hình qua biến môi trường.
"""

import asyncio
import logging
import os
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from faster_whisper import WhisperModel

logger = logging.getLogger('asr')

# Cấu hình qua env (docker-compose truyền vào). Mặc định 'base' — cân bằng cho từ đơn.
MODEL_SIZE = os.getenv('ASR_MODEL', 'base')
MODEL_DIR = os.getenv('ASR_MODEL_DIR', '/models')   # cache model (volume) — không tải lại
LANG = os.getenv('ASR_LANG', 'en')                   # nội dung học là tiếng Anh
# Timeout cho transcription (giây). Web có timeout 20s → ASR nên huỷ sớm hơn.
TRANSCRIBE_TIMEOUT = int(os.getenv('ASR_TIMEOUT', '15'))

app = FastAPI(title='EngForMyChild ASR')


# Nạp model 1 lần lúc khởi động (CPU, int8 cho nhẹ). Lần đầu sẽ TẢI model → chậm.
_model = None
_model_lock = asyncio.Lock()


async def get_model():
    global _model
    if _model is None:
        async with _model_lock:
            # Double-check sau khi giữ lock (phòng multi-worker/async).
            if _model is None:
                loop = asyncio.get_running_loop()
                _model = await loop.run_in_executor(
                    None, lambda: WhisperModel(MODEL_SIZE, device='cpu', compute_type='int8',
                                                download_root=MODEL_DIR))
    return _model


@app.get('/health')
def health():
    """Kiểm tra service sống (web có thể ping trước khi chấm)."""
    return {'ok': True, 'model': MODEL_SIZE}


@app.post('/transcribe')
async def transcribe(audio: UploadFile = File(...)):
    """
    Nhận file audio (webm/wav/mp3...) → trả {'text': '...'} là chuỗi whisper nghe được.

    Không so khớp ở đây — web lo phần đó. Lỗi đọc file/model để FastAPI trả 500,
    web bắt và báo thân thiện (không để bé thấy lỗi).
    """
    # Giới hạn kích thước file upload (10 MB) — tránh OOM.
    MAX_SIZE = 10 * 1024 * 1024
    content = await audio.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail='File audio quá lớn (tối đa 10 MB).')

    # Lưu tạm ra file để faster-whisper đọc (nó nhận đường dẫn/luồng).
    suffix = os.path.splitext(audio.filename or '')[1] or '.webm'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        model = await get_model()

        # Chạy transcription với timeout, chạy trong thread pool để không block event loop.
        loop = asyncio.get_running_loop()

        async def _transcribe():
            segments, _info = await loop.run_in_executor(
                None, lambda: model.transcribe(tmp_path, language=LANG, beam_size=1))
            text = ' '.join(seg.text for seg in segments).strip()
            return {'text': text}

        try:
            return await asyncio.wait_for(_transcribe(), timeout=TRANSCRIBE_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning('Transcription timeout after %ss (file=%s, lang=%s)',
                           TRANSCRIBE_TIMEOUT, audio.filename, LANG)
            raise HTTPException(status_code=504, detail='Transcription timeout.')
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception('Transcription failed (file=%s)', audio.filename)
        raise HTTPException(status_code=500, detail='Transcription error.')
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
