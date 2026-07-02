"""
Service nhập từ vựng từ CSV — dùng chung cho cả lệnh quản trị
(`manage.py import_words`) lẫn màn nhập CSV qua web (catalog views).

Tách ra để KHÔNG copy-paste logic import: idempotent (chạy lại không trùng),
tự sinh IPA khi trống, tự cache audio TTS (có thể tắt). Trả về một dict thống kê.

CSV (có dòng tiêu đề), cột:
    topic        : tên chủ đề (tiếng Anh) — tự tạo Topic nếu chưa có
    text_en      : từ tiếng Anh (BẮT BUỘC)
    text_vi      : nghĩa tiếng Việt
    topic_vi     : (tuỳ chọn) tên chủ đề tiếng Việt khi tạo mới
    level        : (tuỳ chọn) độ khó, mặc định 1
"""

import csv
import io
import logging

from django.utils.text import slugify

from . import audio as audio_service
from . import ipa as ipa_service
from .models import Topic, Word

logger = logging.getLogger('eng.catalog')


class ImportError_(Exception):
    """Lỗi nghiệp vụ khi nhập CSV (vd thiếu cột bắt buộc). Tên có '_' tránh đè built-in."""


def _to_int(value, default):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _get_topic(name_en, name_vi):
    """Lấy/tạo Topic theo slug của tên tiếng Anh (idempotent)."""
    slug = slugify(name_en) or 'general'
    topic, created = Topic.objects.get_or_create(
        slug=slug,
        defaults={'name_en': name_en, 'name_vi': name_vi or name_en},
    )
    return topic, created


def import_rows(reader, make_audio=True, on_progress=None):
    """
    Nhập từ một iterable các dict (vd csv.DictReader). Trả dict thống kê.

    on_progress(message): callback tuỳ chọn để in tiến độ (lệnh CLI dùng);
    màn web bỏ qua. Raise ImportError_ nếu CSV thiếu cột 'text_en'.
    """
    fieldnames = getattr(reader, 'fieldnames', None)
    if fieldnames is not None and 'text_en' not in fieldnames:
        raise ImportError_(
            f"CSV thiếu cột bắt buộc 'text_en'. Tiêu đề hiện có: {fieldnames}")

    stats = {'created_topics': 0, 'created_words': 0, 'updated_words': 0,
             'audio_ok': 0, 'audio_fail': 0, 'skipped': 0}

    for i, row in enumerate(reader, start=2):  # dòng 1 là tiêu đề
        text_en = (row.get('text_en') or '').strip()
        if not text_en:
            stats['skipped'] += 1
            if on_progress:
                on_progress(f'Dòng {i}: bỏ qua (text_en trống).')
            continue

        topic_name = (row.get('topic') or 'General').strip()
        topic, t_created = _get_topic(topic_name, (row.get('topic_vi') or '').strip())
        if t_created:
            stats['created_topics'] += 1

        # Idempotent: tìm theo (topic, text_en); có thì cập nhật nghĩa, chưa có thì tạo.
        word, w_created = Word.objects.get_or_create(
            topic=topic, text_en=text_en,
            defaults={'text_vi': (row.get('text_vi') or '').strip(),
                      'level': _to_int(row.get('level'), 1)},
        )
        if w_created:
            stats['created_words'] += 1
        else:
            new_vi = (row.get('text_vi') or '').strip()
            if new_vi and new_vi != word.text_vi:
                word.text_vi = new_vi
                word.save(update_fields=['text_vi'])
                stats['updated_words'] += 1

        # Sinh IPA nếu chưa có.
        if not word.phonetic:
            phon = ipa_service.to_ipa(text_en)
            if phon:
                word.phonetic = phon
                word.save(update_fields=['phonetic'])

        # Sinh + cache audio (nếu bật và chưa có clip).
        if make_audio and not word.clips.exists():
            clip = audio_service.get_clip(word)
            if clip:
                stats['audio_ok'] += 1
            else:
                stats['audio_fail'] += 1

    return stats


def import_csv_file(file_obj, make_audio=True, on_progress=None):
    """
    Nhập từ một file-like (đã mở dạng text, hoặc bytes từ upload web).

    Chấp nhận: file mở sẵn dạng text, hoặc bytes/str. Bỏ BOM của Excel.
    """
    if isinstance(file_obj, (bytes, bytearray)):
        text = file_obj.decode('utf-8-sig')
        stream = io.StringIO(text)
    elif hasattr(file_obj, 'read'):
        raw = file_obj.read()
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode('utf-8-sig')
        else:
            # text đã đọc: vẫn bỏ BOM nếu có.
            raw = raw.lstrip('﻿')
        stream = io.StringIO(raw)
    else:
        raise ImportError_('Định dạng đầu vào không hỗ trợ.')

    reader = csv.DictReader(stream)
    return import_rows(reader, make_audio=make_audio, on_progress=on_progress)


# --- Xuất (backup) ---
# Cột xuất khớp ĐÚNG cột import (mục 8 trên) → file xuất ra nạp lại được ngay.
# Thêm 'phonetic' để backup đầy đủ IPA; khi nhập lại import bỏ qua cột này và tự sinh
# lại nếu trống, nên không gây lỗi mà vẫn giữ được dữ liệu khi mở bằng Excel.
EXPORT_FIELDS = ['topic', 'topic_vi', 'text_en', 'text_vi', 'phonetic', 'level']


def export_words(queryset=None):
    """
    Xuất từ vựng ra chuỗi CSV (có BOM cho Excel), khớp định dạng nhập → restore được.

    queryset: QuerySet Word tuỳ chọn; mặc định TẤT CẢ từ (kể cả active='N') để
    backup đầy đủ. Sắp theo chủ đề rồi từ cho ổn định (dễ so sánh giữa các lần xuất).
    """
    if queryset is None:
        queryset = Word.objects.all()
    queryset = queryset.select_related('topic').order_by('topic__order', 'topic__name_en', 'text_en')

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=EXPORT_FIELDS)
    writer.writeheader()
    for w in queryset:
        writer.writerow({
            'topic': w.topic.name_en,
            'topic_vi': w.topic.name_vi,
            'text_en': w.text_en,
            'text_vi': w.text_vi,
            'phonetic': w.phonetic,
            'level': w.level,
        })
    # BOM utf-8-sig để Excel mở đúng tiếng Việt; import đã bỏ BOM khi đọc lại.
    return '﻿' + buf.getvalue()
