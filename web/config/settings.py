"""
Cấu hình Django cho dự án EngForMyChild (web học tiếng Anh cho bé).

Nguyên tắc:
- Cấu hình nhạy cảm/đổi theo môi trường đọc từ biến môi trường (.env) — KHÔNG hardcode.
- DB đọc qua DATABASE_URL → đổi SQLite ↔ MySQL chỉ bằng .env, không sửa code
  (xem docs/ThietKeDuLieu.md mục 0.1).
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Thư mục gốc của Django project (chứa manage.py).
BASE_DIR = Path(__file__).resolve().parent.parent

# Nạp biến môi trường từ web/.env (nếu có).
load_dotenv(BASE_DIR / '.env')


def env_bool(name, default=False):
    """Đọc biến môi trường dạng cờ true/false (chuỗi) → bool."""
    return os.getenv(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'y', 'on')


def env_int(name, default):
    """Đọc biến môi trường dạng số nguyên; sai định dạng → dùng default."""
    try:
        return int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        return default


# --- Bảo mật & chế độ chạy ---
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-doi-truoc-khi-len-that')
DEBUG = env_bool('DEBUG', True)
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]
# Cho phép gửi form POST qua tên host khi chạy Docker (vd http://localhost:8000).
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',') if o.strip()]


# --- Ứng dụng ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps nội bộ
    'core',
    'accounts',
    'catalog',
    'pronunciation',
    'games',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Lưu user đang đăng nhập vào thread-local để AuditedModel tự điền created_by/updated_by.
    'core.middleware.CurrentUserMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Template dùng chung (base.html...) đặt ở web/templates/.
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- CSDL ---
# Mặc định SQLite (file db.sqlite3 ở web/). Đổi sang MySQL bằng DATABASE_URL trong .env, vd:
#   DATABASE_URL=mysql://user:pass@db:3306/eng?charset=utf8mb4
# conn_max_age giữ kết nối lại cho MySQL; với MySQL nên kèm charset utf8mb4 (xem ThietKeDuLieu.md 0.1).
DATABASES = {
    'default': dj_database_url.parse(
        os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
    )
}

# Neo file SQLite vào BASE_DIR (web/) để KHÔNG phụ thuộc thư mục chạy lệnh.
# Nếu không, DATABASE_URL tương đối (sqlite:///db.sqlite3) sẽ trỏ tới file khác nhau
# tuỳ chỗ gõ lệnh → dễ tạo admin ở DB này nhưng server đọc DB khác (lỗi "sai mật khẩu" dù đúng).
_db = DATABASES['default']
if _db.get('ENGINE', '').endswith('sqlite3'):
    _name = _db.get('NAME', '')
    if _name and not os.path.isabs(_name):
        _db['NAME'] = str(BASE_DIR / os.path.basename(_name))


# --- Mật khẩu ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Quốc tế hoá ---
# Giao diện tiếng Việt + Anh song song; giờ theo VN. USE_TZ=True để nhất quán giữa SQLite và MySQL.
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True


# --- Tệp tĩnh & media ---
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
# Audio TTS (audio/), hình từ vựng (images/), ghi âm của bé (recordings/) — gắn volume khi chạy Docker.
MEDIA_ROOT = BASE_DIR / 'media'


# --- Đăng nhập ---
LOGIN_URL = 'accounts:login'
# Sau đăng nhập vào thẳng khu của bé (trang chủ). Khu quản lý cần thêm passcode.
LOGIN_REDIRECT_URL = 'accounts:home'
LOGOUT_REDIRECT_URL = 'accounts:login'


# --- Phiên đăng nhập (sống lâu để phụ huynh ít phải đăng nhập lại — app local) ---
# Mặc định 30 ngày; SAVE_EVERY_REQUEST=True → mỗi request gia hạn lại (trượt hạn).
SESSION_COOKIE_AGE = env_int('SESSION_DAYS', 30) * 86400
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# --- Khu quản lý: passcode (lớp khoá thứ 2 sau đăng nhập, để bé không tự vào) ---
# Mở khoá giữ trong N phút không thao tác (trượt hạn) — xem core.decorators.manage_required.
MANAGE_UNLOCK_MINUTES = env_int('MANAGE_UNLOCK_MINUTES', 30)


# --- Khoá chính mặc định ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Cấu hình riêng dự án (đọc từ .env) ---
# URL service ASR (faster-whisper) — dùng từ GĐ 3. Giọng TTS mặc định cho edge-tts.
ASR_URL = os.getenv('ASR_URL', 'http://asr:9000')
TTS_VOICE = os.getenv('TTS_VOICE', 'en-US-AnaNeural')  # giọng trẻ em, rõ ràng
# Giọng tiếng Việt (Neural, tự nhiên) cho lời động viên khi bé chơi game.
TTS_VOICE_VI = os.getenv('TTS_VOICE_VI', 'vi-VN-HoaiMyNeural')


# --- Logging ---
# Ghi log ra console + 3 file tên theo ngày trong LOG_DIR (mặc định web/logs/):
#   app-YYYY-MM-DD.log      (INFO trở lên — hoạt động chung)
#   error-YYYY-MM-DD.log    (ERROR trở lên — lỗi, có traceback)
#   security-YYYY-MM-DD.log (django.security — đăng nhập sai, CSRF...)
# File xoay vòng nửa đêm, giữ 30 ngày. Mức log chỉnh qua LOG_LEVEL trong .env.
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = os.getenv('LOG_DIR', str(BASE_DIR / 'logs'))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{asctime} [{levelname}] {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
        'app_file': {
            'class': 'config.logging_utils.DailyFileHandler',
            'log_dir': LOG_DIR, 'prefix': 'app',
            'level': 'INFO', 'formatter': 'verbose',
        },
        'error_file': {
            'class': 'config.logging_utils.DailyFileHandler',
            'log_dir': LOG_DIR, 'prefix': 'error',
            'level': 'ERROR', 'formatter': 'verbose',
        },
        'security_file': {
            'class': 'config.logging_utils.DailyFileHandler',
            'log_dir': LOG_DIR, 'prefix': 'security',
            'level': 'INFO', 'formatter': 'verbose',
        },
    },
    'loggers': {
        # Logger nội bộ dự án: dùng logging.getLogger('eng') / 'eng.tts' / 'eng.asr'...
        'eng': {
            'handlers': ['console', 'app_file', 'error_file'],
            'level': LOG_LEVEL, 'propagate': False,
        },
        # Log của Django (request, server) → file app + error.
        'django': {
            'handlers': ['console', 'app_file', 'error_file'],
            'level': 'INFO', 'propagate': False,
        },
        # Sự kiện bảo mật (đăng nhập sai, CSRF...) → file security riêng.
        'django.security': {
            'handlers': ['console', 'security_file'],
            'level': 'INFO', 'propagate': False,
        },
    },
    'root': {'handlers': ['console', 'error_file'], 'level': 'WARNING'},
}
