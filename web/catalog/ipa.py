"""
Sinh phiên âm IPA cho từ tiếng Anh bằng thư viện eng-to-ipa.

Tách riêng để: dễ test (mock được), và chịu được khi thư viện chưa cài
(trả chuỗi rỗng thay vì làm sập import của app).
"""

import logging

logger = logging.getLogger('eng.ipa')


def to_ipa(text_en):
    """
    Trả về IPA của một từ/cụm tiếng Anh, vd 'cat' -> 'kæt'.

    Trả '' nếu thư viện chưa cài hoặc không tra được (eng-to-ipa đánh dấu từ
    không tra được bằng dấu '*'). Không raise — IPA là phần phụ trợ.
    """
    text_en = (text_en or '').strip()
    if not text_en:
        return ''
    try:
        import eng_to_ipa as ipa
    except ImportError:
        logger.warning('Chưa cài eng-to-ipa — bỏ qua sinh IPA.')
        return ''
    try:
        result = ipa.convert(text_en)
    except Exception:
        logger.exception('Lỗi sinh IPA cho %r', text_en)
        return ''
    # eng-to-ipa giữ nguyên từ kèm '*' khi không tra được → coi như không có IPA.
    if '*' in result:
        return ''
    return result.strip()
