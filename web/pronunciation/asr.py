"""
Chấm phát âm cho bé — gọi service ASR (faster-whisper) rồi SO KHỚP mức từ.

Kiến trúc: nhận dạng giọng nằm ở service `asr` riêng (Docker); file này chỉ
điều phối — gọi HTTP, so text bé đọc với từ đích, quy ra 0–3 sao KHÍCH LỆ.

Nguyên tắc (skill eng-coding mục 6):
- Chấm = sao khích lệ, KHÔNG điểm gây áp lực; sai thì khuyến khích nghe lại.
- Lỗi mạng/ASR tắt/timeout → trả None, KHÔNG raise 500; view báo "thử lại" thân thiện.
- Giọng bé chỉ tới service local (ASR_URL), không gửi ra ngoài.

Tách riêng để MOCK trong test (không gọi service thật).
"""

import logging
import re
from difflib import SequenceMatcher

import requests
from django.conf import settings

logger = logging.getLogger('eng.asr')

# Ngưỡng quy sao cho PHÁT ÂM (nới hơn game vì ASR khó khớp tuyệt đối, và để khích lệ):
#   >=85% → 3 sao | >=60% → 2 sao | >=35% → 1 sao | còn lại → 0 (mầm 🌱).
STAR_THRESHOLDS = ((85, 3), (60, 2), (35, 1))


def _digits_to_words(text):
    """Chuyển số thành chữ tiếng Anh trong text (vd '11' → 'eleven')."""
    _ONES = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
             'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
             'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
    _TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy',
             'eighty', 'ninety']

    def _convert(n):
        """Chuyển số nguyên (int) 0-999 thành chữ."""
        if n < 20:
            return _ONES[n]
        if n < 100:
            ten, one = divmod(n, 10)
            return _TENS[ten] + (f' {_ONES[one]}' if one else '')
        hundred, rest = divmod(n, 100)
        return _ONES[hundred] + ' hundred' + (f' {_convert(rest)}' if rest else '')

    def _replace(m):
        n = int(m.group())
        # Chỉ chuyển số trong khoảng từ vựng có thể có (0-999).
        if 0 <= n <= 999:
            return _convert(n)
        return m.group()

    return re.sub(r'\d+', _replace, text)


def _normalize(text):
    """Chuẩn hoá để so khớp: thường hoá, bỏ dấu câu, chuyển số→chữ, gộp khoảng trắng."""
    text = (text or '').lower().strip()
    text = re.sub(r"[^a-z0-9\s']", ' ', text)   # bỏ dấu câu, giữ chữ/số/nháy
    text = _digits_to_words(text)                # '11' → 'eleven'
    return re.sub(r'\s+', ' ', text).strip()


def match_score(heard, target):
    """
    Độ khớp 0–100 giữa chuỗi máy nghe được (heard) và từ đích (target).

    Dùng SequenceMatcher trên chuỗi đã chuẩn hoá. Khớp hoàn toàn = 100.
    (Tách riêng, thuần — dễ test không cần HTTP.)
    """
    h, t = _normalize(heard), _normalize(target)
    if not t:
        return 0
    ratio = SequenceMatcher(None, h, t).ratio()
    return round(ratio * 100)


def stars_from_score(score):
    """Quy điểm khớp 0–100 → sao 0–3 theo ngưỡng khích lệ của phát âm."""
    for threshold, stars in STAR_THRESHOLDS:
        if score >= threshold:
            return stars
    return 0


def transcribe(audio_file):
    """
    Gọi service ASR → trả text nghe được, hoặc None nếu lỗi (không raise).

    audio_file: đối tượng file (InMemoryUploadedFile / mở từ FieldFile).
    """
    url = settings.ASR_URL.rstrip('/') + '/transcribe'
    try:
        # Đưa con trỏ về đầu (phòng file đã đọc trước đó).
        try:
            audio_file.seek(0)
        except (AttributeError, OSError):
            pass
        files = {'audio': (getattr(audio_file, 'name', 'rec.webm'), audio_file)}
        resp = requests.post(url, files=files, timeout=settings.ASR_TIMEOUT)
        resp.raise_for_status()
        return (resp.json() or {}).get('text', '')
    except Exception:
        # ASR tắt/timeout/mạng → không chấm được, để bên gọi xử lý thân thiện.
        logger.warning('Không gọi được ASR tại %s', url, exc_info=True)
        return None


def score(audio_file, target_en):
    """
    Chấm một lần đọc. Trả dict hoặc None (khi ASR không phản hồi).

    dict: {'heard': str, 'target': str, 'score': 0-100, 'stars': 0-3}.
    """
    heard = transcribe(audio_file)
    if heard is None:
        return None
    s = match_score(heard, target_en)
    return {'heard': heard, 'target': target_en, 'score': s, 'stars': stars_from_score(s)}
