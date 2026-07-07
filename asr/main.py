"""
Service chấm phát âm (ASR) — FastAPI + faster-whisper. Chạy RIÊNG trong Docker.

Nhiệm vụ tối giản: nhận file audio bé đọc → trả text nghe được. Việc SO KHỚP với
từ đích và quy ra sao nằm ở web (pronunciation/asr.py) — service này chỉ nhận dạng.

Giọng bé chỉ tới service local này, KHÔNG gửi ra ngoài (whisper chạy offline sau
khi đã tải model về volume). Model + ngôn ngữ cấu hình qua biến môi trường.
"""

import os
import tempfile

from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel

# Cấu hình qua env (docker-compose truyền vào). Mặc định 'base' — cân bằng cho từ đơn.
MODEL_SIZE = os.getenv('ASR_MODEL', 'base')
MODEL_DIR = os.getenv('ASR_MODEL_DIR', '/models')   # cache model (volume) — không tải lại
LANG = os.getenv('ASR_LANG', 'en')                   # nội dung học là tiếng Anh

app = FastAPI(title='EngForMyChild ASR')

# Nạp model 1 lần lúc khởi động (CPU, int8 cho nhẹ). Lần đầu sẽ TẢI model → chậm.
_model = None


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(MODEL_SIZE, device='cpu', compute_type='int8',
                              download_root=MODEL_DIR)
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
    # Lưu tạm ra file để faster-whisper đọc (nó nhận đường dẫn/luồng).
    suffix = os.path.splitext(audio.filename or '')[1] or '.webm'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        segments, _info = get_model().transcribe(tmp_path, language=LANG, beam_size=1)
        text = ' '.join(seg.text for seg in segments).strip()
        return {'text': text}
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
