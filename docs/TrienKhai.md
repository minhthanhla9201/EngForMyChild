# Hướng dẫn triển khai EngForMyChild

Tài liệu hướng dẫn đưa ứng dụng **EngForMyChild** (web học tiếng Anh cho bé — Django 4.2) vào sử dụng thật theo 3 cách:

| Option | Phù hợp | CSDL | Độ phức tạp |
|--------|---------|------|-------------|
| **1. Local (SQLite3) + ASR Docker** | Dùng trên 1 máy (hoặc vài thiết bị trong LAN) | SQLite (1 file) | ⭐ Dễ nhất |
| **2. Docker** | Đóng gói chạy trên 1 server (Linux/NAS/VPS), dễ di chuyển | MySQL/MariaDB (trong container) | ⭐⭐ Trung bình |
| **3. Host thật + MySQL** | Nhiều người dùng, có tên miền + HTTPS | MySQL/MariaDB | ⭐⭐⭐ Cao |

> **Kiến trúc:** app gồm 2 phần — **web** (Django, thư mục `web/`) và **service ASR** (faster-whisper chấm phát âm, thư mục `asr/`, chạy trong Docker, publish cổng 9000). Web gọi ASR qua HTTP (biến `ASR_URL`). TTS (edge-tts) và ghi âm của bé sinh ra file trong `web/media/`.

> **Nguyên tắc chung cho mọi option** (KHÔNG bao giờ bỏ qua khi chạy thật):
> - `DEBUG=False`.
> - `SECRET_KEY` mới, ngẫu nhiên (không dùng key dev trong repo).
> - Khai báo đúng `ALLOWED_HOSTS` (và `CSRF_TRUSTED_ORIGINS` nếu truy cập qua IP/tên miền).
> - **Không dùng `runserver`** cho chạy thật — dùng `waitress` (Windows) hoặc `gunicorn` (Linux/Docker).
> - File tĩnh (CSS/JS) phục vụ qua **WhiteNoise** (khi `DEBUG=False`, Django không tự phục vụ static).
> - File **media** (audio TTS, ảnh từ vựng, ghi âm của bé trong `web/media/`) — xem [mục 0.3](#03-phục-vụ-file-media-audioảnhghi-âm). Đây là điểm dễ quên nhất: nếu không cấu hình, mọi audio/ảnh sẽ **404** khi `DEBUG=False`.
> - Đổi mật khẩu tài khoản `admin` mặc định.

---

## 0. Chuẩn bị chung (làm 1 lần cho cả 3 option)

### 0.1. Bổ sung thư viện

`web/requirements.txt` đã có sẵn `whitenoise` và `waitress`. Nếu triển khai Docker/Linux (Option 2, 3) thì thêm:
```
gunicorn>=21.2       # WSGI server cho Linux/Docker (Option 2, 3)
mysqlclient>=2.2     # driver MySQL (Option 2, 3)
```
> Option 1 (SQLite/Windows) chỉ cần `whitenoise` + `waitress` (đã có trong `web/requirements.txt`).

### 0.2. WhiteNoise cho file tĩnh (đã cấu hình sẵn)

Các thay đổi dưới đây **đã có** trong `web/config/settings.py` — nêu ở đây để bạn hiểu, không cần sửa lại:

**a) WhiteNoise** trong `MIDDLEWARE`, ngay **sau** `SecurityMiddleware`:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # phục vụ static khi DEBUG=False
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... giữ nguyên các dòng còn lại
]
```

**b) Nén & cache file tĩnh:**
```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```
> ⚠️ Với storage này, **bắt buộc chạy `collectstatic` trước** khi bật `DEBUG=False`, nếu không static (CSS/JS) sẽ lỗi.

**c) `ALLOWED_HOSTS` và `CSRF_TRUSTED_ORIGINS`** đọc từ `.env` (đã có sẵn trong settings, cách nhau bằng dấu phẩy).

### 0.3. Phục vụ file media (audio/ảnh/ghi âm)

**Đây là điểm khác biệt then chốt so với static.** Media của app **sinh lúc chạy** (edge-tts sinh mp3, bé ghi âm mới) nên **KHÔNG dùng WhiteNoise** — WhiteNoise chỉ quét thư mục **một lần lúc khởi động**, file sinh sau sẽ 404 tới khi restart.

Cách đúng: để Django phục vụ media qua view `serve` (đọc đĩa **mỗi request** → luôn thấy file mới). Đã cấu hình trong `web/config/urls.py`:
```python
import re
from django.conf import settings
from django.urls import re_path
from django.views.static import serve

# Media sinh runtime → serve đọc đĩa mỗi request. Đăng ký TRỰC TIẾP bằng re_path
# (KHÔNG dùng helper static() vì nó tự no-op khi DEBUG=False), để hoạt động cả khi DEBUG=False.
_media_prefix = settings.MEDIA_URL.lstrip('/')
urlpatterns += [
    re_path(r'^%s(?P<path>.*)$' % re.escape(_media_prefix), serve, {'document_root': settings.MEDIA_ROOT}),
]
```
> Cách này hợp cho **Option 1** (chạy local, không có web server ngoài). Với **Option 2/3** có nginx/Caddy đứng trước, nên để web server đó phục vụ `/media/` (nhanh hơn) — xem mục tương ứng.

### 0.4. Sinh SECRET_KEY mới
```powershell
# Windows
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```
```bash
# Linux
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

---

## Option 1 — Local, SQLite3, cho 1 máy

Đơn giản nhất: 1 file `db.sqlite3`, không cần cài CSDL server. Web chạy bằng `waitress`, service ASR chạy trong Docker. Phù hợp 1 người dùng (hoặc vài thiết bị trong cùng wifi). Hướng dẫn này dành cho **máy tính hoàn toàn mới (chưa cài gì)**.

### 1.1. Cài đặt Python
1. Truy cập [python.org/downloads](https://www.python.org/downloads/) và tải bộ cài đặt Python mới nhất (vd: 3.11 hoặc 3.12).
2. Chạy file cài đặt, **BẮT BUỘC TICK VÀO Ô "Add python.exe to PATH"** ở màn hình đầu tiên.
3. Bấm *Install Now* và đợi hoàn tất.
4. Mở **PowerShell**, gõ `python --version` để kiểm tra. Nếu hiện ra phiên bản Python là thành công.

### 1.2. Tải mã nguồn
1. Tải mã nguồn (file `.zip` giải nén, hoặc `git clone`).
2. Đặt ở nơi dễ quản lý, ví dụ: `D:\EngForMyChild`.

### 1.3. Tạo môi trường ảo và cài đặt thư viện
Mở **PowerShell**, di chuyển tới thư mục dự án:
```powershell
# Chuyển tới thư mục dự án (thay đường dẫn thực tế của bạn)
cd D:\EngForMyChild

# Tạo môi trường ảo (chỉ làm 1 lần)
python -m venv .venv

# Cài đặt thư viện web
.\.venv\Scripts\python.exe -m pip install -r web\requirements.txt
```

### 1.4. Tạo `web/.env` cho chạy thật
Tạo file tên đúng là `.env` (không có đuôi .txt) trong thư mục `web` (mẫu: `web/.env.example`):
```ini
DEBUG=False
SECRET_KEY=dan-key-vua-sinh-o-buoc-0.4
# Chỉ máy này: 127.0.0.1,localhost
# Cho thiết bị khác trong LAN: thêm IP LAN của máy (vd 192.168.1.50)
ALLOWED_HOSTS=127.0.0.1,localhost,192.168.1.50
CSRF_TRUSTED_ORIGINS=http://192.168.1.50:9001,http://localhost:9001
# Service ASR chạy Docker: container nghe 9000, publish ra host 9002 (xem docker-compose.yml)
ASR_URL=http://localhost:9002
# Phiên đăng nhập sống bao nhiêu ngày (trượt hạn mỗi request)
SESSION_DAYS=30
LOG_LEVEL=INFO
# Để trống DATABASE_URL = dùng SQLite (web/db.sqlite3)
```
> Tìm IP LAN: trong PowerShell gõ `ipconfig | Select-String "IPv4"`. Nên đặt **IP tĩnh** cho máy để IP không đổi sau khi khởi động lại máy/router.

### 1.5. Tạo bảng + gom static + tài khoản
Vẫn trong **PowerShell** tại thư mục dự án (`D:\EngForMyChild`):
```powershell
.\.venv\Scripts\python.exe web\manage.py migrate
.\.venv\Scripts\python.exe web\manage.py collectstatic --noinput
.\.venv\Scripts\python.exe web\manage.py createsuperuser
.\.venv\Scripts\python.exe web\manage.py check --deploy   # xem cảnh báo bảo mật
```

### 1.6. Chạy service ASR (chấm phát âm) bằng Docker
ASR là service riêng (faster-whisper). Cần cài **Docker Desktop** trước ([docker.com](https://www.docker.com/products/docker-desktop/)).
```powershell
# Tại thư mục gốc dự án — build + chạy nền service asr
docker compose up -d asr
```
> Lần đầu sẽ tải model Whisper (cache trong volume `asr_models`, không tải lại lần sau). Container nghe cổng 9000, publish ra host **9002** → khớp `ASR_URL=http://localhost:9002` ở bước 1.4.
> Nếu không cần chấm phát âm ngay, có thể bỏ qua bước này — các phần khác (từ vựng, trò chơi, nghe TTS) vẫn chạy.

### 1.7. Mở firewall (nếu cho LAN truy cập) — PowerShell *Administrator*
Mở PowerShell bằng quyền Administrator (chuột phải > Run as Administrator):
```powershell
New-NetFirewallRule -DisplayName "EngForMyChild 9001" -Direction Inbound -LocalPort 9001 -Protocol TCP -Action Allow
```

### 1.8. Chạy server web
File `start_tsm.bat` ở thư mục gốc dự án:
```bat
@echo off
REM Di chuyển vào thư mục web
cd /d "%~dp0web"
REM Chạy waitress từ môi trường ảo
..\.venv\Scripts\python.exe -m waitress --listen=0.0.0.0:9001 config.wsgi:application
```
Bấm đúp `start_tsm.bat` để chạy server (sẽ có 1 cửa sổ đen hiện ra, cần giữ nó luôn mở).
**(Để dừng server: tắt cửa sổ đen này, hoặc bấm `Ctrl + C` bên trong cửa sổ.)**

Truy cập ứng dụng:
- Trên máy chạy server: `http://127.0.0.1:9001`
- Thiết bị khác trong mạng LAN: `http://192.168.1.50:9001` (thay IP LAN của bạn)

> **Kiểm tra media:** mở một bài từ vựng và bấm nghe. Nếu **không có tiếng** (audio 404), kiểm tra lại route media ở [mục 0.3](#03-phục-vụ-file-media-audioảnhghi-âm) và thư mục `web/media/audio/` có file `.mp3` không.

### 1.9. Tự khởi động cùng Windows (tuỳ chọn)
- **Task Scheduler:** Create Task → Triggers *"At log on"* → Actions: chạy `start_tsm.bat`. Tick *"Run whether user is logged on or not"* nếu muốn chạy nền.
- Hoặc dùng **NSSM** (chạy như Windows Service): `nssm install EngForMyChild` rồi trỏ tới `python.exe` trong `.venv` kèm tham số waitress.
- Docker Desktop nên đặt **tự khởi động cùng Windows** để service ASR luôn sẵn sàng.

### 1.10. 🔒 Sao lưu (BACKUP)

CSDL SQLite là **1 file duy nhất** `web/db.sqlite3` → sao lưu = chép file này sang chỗ an toàn. Thư mục `web/media/` (audio, ảnh, ghi âm của bé) cũng nên sao lưu nếu muốn giữ nội dung đã sinh.

**Cách A — chép file (đơn giản, khuyên dùng):**
Nên tắt server vài giây, copy `web/db.sqlite3` ra chỗ khác rồi bật lại:
```powershell
Copy-Item web\db.sqlite3 "D:\backup\eng-$(Get-Date -Format yyyyMMdd-HHmm).sqlite3"
```

**Cách B — sao lưu logic (không cần tắt server, dạng JSON):**
```powershell
.\.venv\Scripts\python.exe web\manage.py dumpdata --natural-foreign --natural-primary `
  -e contenttypes -e auth.permission --indent 2 -o "D:\backup\eng-$(Get-Date -Format yyyyMMdd).json"
```

**Cách C — tự động sao lưu lên GitHub Release** (script `backup_tsm.bat`):

> ⚠️ **BẢO MẬT — đọc kỹ:** `db.sqlite3` chứa **hash mật khẩu tài khoản** và dữ liệu học tập của bé. Cách này đẩy nguyên CSDL lên GitHub, nên **repo PHẢI luôn để chế độ private**. Nếu lỡ đổi repo sang *public*, **toàn bộ các bản backup cũ trong Releases sẽ bị lộ ngay**. An toàn hơn: dùng **một repo private RIÊNG cho backup**, hoặc mã hoá file zip trước khi upload. Nếu chỉ cần đơn giản, **Cách A (chép file ra ổ khác / cloud)** là đủ và an toàn nhất.

Script `backup_tsm.bat` ở thư mục gốc dự án (tự dọn, chỉ giữ **14 bản** release gần nhất):
```bat
@echo off
setlocal

REM ==================================================
REM Chuyển vào thư mục web
REM ==================================================
cd /d "%~dp0web"

echo.
echo ==========================================
echo BAT DAU BACKUP SQLITE LEN GITHUB RELEASE
echo ==========================================
echo.

REM ==================================================
REM Tạo timestamp (vd: backup-20260616-223015)
REM ==================================================
for /f %%i in (
    'powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"'
) do (
    set TAG=backup-%%i
)

echo [INFO] Tag: %TAG%

REM ==================================================
REM Kiểm tra database
REM ==================================================
if not exist db.sqlite3 (
    echo [ERROR] Khong tim thay file db.sqlite3
    exit /b 1
)

REM ==================================================
REM Tạo thư mục backup + tên file
REM ==================================================
if not exist backup ( mkdir backup )
set SQLITE_FILE=backup\backup.sqlite3
set ZIP_FILE=backup\%TAG%.zip

REM ==================================================
REM Copy database
REM ==================================================
echo [INFO] Dang sao chep database...
copy /Y db.sqlite3 "%SQLITE_FILE%" >nul
if errorlevel 1 (
    echo [ERROR] Khong the sao chep database
    exit /b 1
)

REM ==================================================
REM Nén database
REM ==================================================
if exist "%ZIP_FILE%" del /q "%ZIP_FILE%"
echo [INFO] Dang nen database...
powershell -NoProfile -Command ^
"Compress-Archive -Path '%SQLITE_FILE%' -DestinationPath '%ZIP_FILE%' -Force -ErrorAction Stop"
if errorlevel 1 (
    echo [ERROR] Khong the tao file ZIP
    del /q "%SQLITE_FILE%" 2>nul
    exit /b 1
)
echo [INFO] Da tao: %ZIP_FILE%

REM ==================================================
REM Kiểm tra GitHub CLI
REM ==================================================
gh auth status >nul 2>&1
if errorlevel 1 (
    echo [ERROR] GitHub CLI chua dang nhap. Chay: gh auth login
    del /q "%SQLITE_FILE%" 2>nul
    del /q "%ZIP_FILE%" 2>nul
    exit /b 1
)

REM ==================================================
REM Tạo GitHub Release (gh tự tạo tag nếu chưa có)
REM ==================================================
echo [INFO] Dang upload len GitHub Release...
gh release create %TAG% "%ZIP_FILE%" ^
    --title "%TAG%" ^
    --notes "Automatic SQLite backup"
if errorlevel 1 (
    echo [ERROR] Tao GitHub Release that bai
    del /q "%SQLITE_FILE%" 2>nul
    del /q "%ZIP_FILE%" 2>nul
    exit /b 1
)

REM ==================================================
REM Dọn file tạm
REM ==================================================
del /q "%SQLITE_FILE%" 2>nul
del /q "%ZIP_FILE%" 2>nul

REM ==================================================
REM Don release backup cu (giu 14 ban moi nhat)
REM ==================================================
echo [INFO] Dang don release backup cu (giu 14 ban moi nhat)...
powershell -NoProfile -Command ^
"$keep=14; gh release list --limit 200 --json tagName,createdAt | ConvertFrom-Json | Where-Object { $_.tagName -like 'backup-*' } | Sort-Object createdAt -Descending | Select-Object -Skip $keep | ForEach-Object { Write-Host ('[INFO] Xoa release cu: ' + $_.tagName); gh release delete $_.tagName --yes --cleanup-tag }"

echo.
echo ==========================================
echo BACKUP THANH CONG
echo ==========================================
echo.
exit /b 0
```

**Cài đặt GitHub CLI:**
1. Tải & cài: https://cli.github.com/
2. Kiểm tra: `gh --version`
3. Đăng nhập: `gh auth login`

→ Đặt Task Scheduler chạy `backup_tsm.bat` hằng ngày (vd 23:00). Nên đồng bộ thư mục `D:\backup` lên cloud (OneDrive, Google Drive).

### 1.11. ♻️ Khôi phục (RESTORE)
1. **Tắt server** (đóng cửa sổ `start_tsm.bat`).
2. Chép bản sao đè lên file hiện tại:
   ```powershell
   Copy-Item "D:\backup\eng-20260612.sqlite3" web\db.sqlite3 -Force
   ```
3. Bấm đúp `start_tsm.bat` chạy lại server.

> Khôi phục từ bản JSON (Cách B): tạo DB trống mới (`migrate`) rồi chạy `.\.venv\Scripts\python.exe web\manage.py loaddata D:\backup\eng-20260612.json`.

**Khôi phục từ GitHub Release (Cách C):**
1. Xem danh sách bản backup: `gh release list`
2. **Tắt server**, tải bản cần khôi phục về thư mục `web` và giải nén:
   ```powershell
   cd web
   gh release download backup-20260616-223015        # thay bằng tag bản cần khôi phục
   Expand-Archive .\backup-20260616-223015.zip -DestinationPath . -Force
   Copy-Item .\backup.sqlite3 .\db.sqlite3 -Force     # file trong zip tên backup.sqlite3
   Remove-Item .\backup.sqlite3, .\backup-20260616-223015.zip
   ```
3. Bấm đúp `start_tsm.bat` chạy lại server.

---

## Option 2 — Docker (đóng gói, dễ di chuyển)

Đóng gói **web + MariaDB + ASR** thành các container, chạy bằng `docker compose`. Phù hợp khi triển khai lên 1 server Linux / NAS / VPS đã cài Docker.

> Lưu ý: `docker-compose.yml` trong repo hiện chỉ bật service **asr** (web chạy local). Bên dưới là cấu hình đầy đủ cho trường hợp chạy **web trong Docker luôn** — bổ sung service `web` và `db`.

### 2.1. Tạo `web/Dockerfile`
```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# Thư viện hệ thống để build mysqlclient
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn mysqlclient

COPY . .

# Gom file tĩnh ngay khi build (collectstatic không cần DB)
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

### 2.2. Tạo `.dockerignore` ở thư mục gốc
```
.venv/
**/__pycache__/
web/db.sqlite3
web/logs/
web/staticfiles/
.git/
docs/
*.md
asr/models/
```

### 2.3. Bổ sung `docker-compose.yml` (thêm service web + db)
Thêm vào `docker-compose.yml` (giữ service `asr` sẵn có):
```yaml
services:
  db:
    image: mariadb:11
    environment:
      MARIADB_DATABASE: eng
      MARIADB_USER: eng
      MARIADB_PASSWORD: ${DB_PASSWORD}
      MARIADB_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  web:
    build: ./web
    environment:
      DEBUG: "False"
      SECRET_KEY: ${SECRET_KEY}
      ALLOWED_HOSTS: ${ALLOWED_HOSTS}
      CSRF_TRUSTED_ORIGINS: ${CSRF_TRUSTED_ORIGINS}
      DATABASE_URL: mysql://eng:${DB_PASSWORD}@db:3306/eng
      ASR_URL: http://asr:9000          # trong mạng Docker, gọi ASR qua tên service
    volumes:
      - media_data:/app/media           # GIỮ media (audio TTS, ghi âm bé) qua các lần chạy
    depends_on:
      db:
        condition: service_healthy
      asr:
        condition: service_started
    ports:
      - "9001:8000"
    restart: unless-stopped

volumes:
  db_data:
  media_data:
```
> - MariaDB 11 mặc định charset `utf8mb4` → tiếng Việt OK.
> - **Media** ở đây được gắn **named volume** `media_data` để không mất khi rebuild container. Django tự phục vụ `/media/` qua route ở [mục 0.3](#03-phục-vụ-file-media-audioảnhghi-âm) (không có nginx trong compose này). Nếu đặt reverse proxy trước, xem mục 2.7.
> - `ASR_URL=http://asr:9000` — trong mạng Docker gọi qua tên service `asr`, KHÔNG phải `localhost`.

### 2.4. Tạo `.env` cho compose (cùng cấp `docker-compose.yml`)
```ini
SECRET_KEY=key-ngau-nhien-da-sinh
DB_PASSWORD=mat-khau-db-manh
DB_ROOT_PASSWORD=mat-khau-root-manh
ALLOWED_HOSTS=ten-mien-hoac-ip-server,localhost
CSRF_TRUSTED_ORIGINS=http://ip-server:9001
```
> ⚠️ Thêm `.env` chứa bí mật vào `.gitignore` (đã có `web/.env`; file `.env` ở gốc cũng nên bỏ qua git).

### 2.5. Khởi chạy
```bash
docker compose up -d --build              # build image + chạy nền (web, db, asr)
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```
Truy cập `http://<ip-server>:9001`. Xem log: `docker compose logs -f web`.

### 2.6. 🔒 Backup & ♻️ Restore
```bash
# Backup CSDL
docker compose exec db sh -c 'exec mariadb-dump -u root -p"$MARIADB_ROOT_PASSWORD" eng' > eng-$(date +%F).sql

# Restore CSDL
cat eng-2026-06-12.sql | docker compose exec -T db sh -c 'exec mariadb -u root -p"$MARIADB_ROOT_PASSWORD" eng'

# Backup media (audio/ảnh/ghi âm) — copy từ named volume
docker compose cp web:/app/media ./media-backup-$(date +%F)
```
> CSDL nằm trong volume `db_data`, media trong `media_data` (vẫn còn khi container bị xoá). Nên thêm lệnh backup vào cron của server và đẩy file ra nơi an toàn.

### 2.7. (Tuỳ chọn) HTTPS + phục vụ media qua reverse proxy
Đặt reverse proxy (nginx / Caddy / Traefik) trước container `web`, lo TLS. Caddy gọn nhất (tự xin chứng chỉ Let's Encrypt). Khi đó nên cho proxy phục vụ trực tiếp `/media/` (nhanh hơn Django) bằng cách mount `media_data` vào proxy, và đặt `CSRF_TRUSTED_ORIGINS=https://ten-mien.com`.

---

## Option 3 — Host thật + MySQL (production, có HTTPS)

Triển khai trên server Linux thật (vd Ubuntu 22.04) với **MySQL/MariaDB + gunicorn + nginx + HTTPS**. Service ASR chạy trong Docker (hoặc container riêng). Phù hợp nhiều người dùng, có tên miền.

### 3.1. Cài gói hệ thống
```bash
sudo apt update
sudo apt install -y python3-venv python3-dev build-essential pkg-config \
                    default-libmysqlclient-dev mariadb-server nginx git docker.io docker-compose-plugin
```

### 3.2. Tạo CSDL (lưu ý `utf8mb4` cho tiếng Việt)
```bash
sudo mariadb
```
```sql
CREATE DATABASE eng CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'eng'@'localhost' IDENTIFIED BY 'mat-khau-manh';
GRANT ALL PRIVILEGES ON eng.* TO 'eng'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3.3. Lấy mã nguồn + môi trường ảo
```bash
cd /opt
sudo git clone <repo-url> eng && cd eng
sudo python3 -m venv .venv
sudo .venv/bin/pip install -r web/requirements.txt gunicorn mysqlclient
```

### 3.4. Chạy service ASR (Docker)
```bash
cd /opt/eng
sudo docker compose up -d asr        # publish cổng 9000
```

### 3.5. Tạo `web/.env`
```ini
DEBUG=False
SECRET_KEY=key-ngau-nhien-da-sinh
ALLOWED_HOSTS=eng.ten-mien.com
CSRF_TRUSTED_ORIGINS=https://eng.ten-mien.com
DATABASE_URL=mysql://eng:mat-khau-manh@127.0.0.1:3306/eng
# Web (gunicorn) chạy local, ASR trong Docker publish host 9002
ASR_URL=http://localhost:9002
LOG_LEVEL=INFO
```

### 3.6. Khởi tạo dữ liệu + file tĩnh
```bash
.venv/bin/python web/manage.py migrate
.venv/bin/python web/manage.py collectstatic --noinput
.venv/bin/python web/manage.py createsuperuser
.venv/bin/python web/manage.py check --deploy
```

### 3.7. Chạy gunicorn như systemd service
Tạo `/etc/systemd/system/eng.service`:
```ini
[Unit]
Description=EngForMyChild (Django) gunicorn
After=network.target mariadb.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/eng/web
ExecStart=/opt/eng/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:9001 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now eng
sudo systemctl status eng
```

### 3.8. nginx reverse proxy + phục vụ static & media
Tạo `/etc/nginx/sites-available/eng`:
```nginx
server {
    listen 80;
    server_name eng.ten-mien.com;

    location /static/ {
        alias /opt/eng/web/staticfiles/;
    }
    # Media (audio TTS, ảnh, ghi âm của bé) — nginx phục vụ trực tiếp, nhanh hơn Django
    location /media/ {
        alias /opt/eng/web/media/;
    }
    location / {
        proxy_pass http://127.0.0.1:9001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Ghi âm của bé có thể lớn — nới giới hạn upload
        client_max_body_size 25M;
    }
}
```
> Khi nginx đã phục vụ `/media/`, route media của Django ở [mục 0.3](#03-phục-vụ-file-media-audioảnhghi-âm) trở nên thừa (nginx bắt request trước) — không sao, cứ để nguyên.
```bash
sudo ln -s /etc/nginx/sites-available/eng /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 3.9. Bật HTTPS (Let's Encrypt)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d eng.ten-mien.com
```
Certbot tự sửa nginx sang HTTPS + tự gia hạn. Đảm bảo `CSRF_TRUSTED_ORIGINS=https://eng.ten-mien.com`.

### 3.10. 🔒 Backup & ♻️ Restore
```bash
# Backup CSDL (đặt vào cron hằng ngày)
mysqldump -u eng -p eng > /opt/backup/eng-$(date +%F).sql
# Backup media
tar czf /opt/backup/media-$(date +%F).tar.gz -C /opt/eng/web media

# Restore CSDL
mysql -u eng -p eng < /opt/backup/eng-2026-06-12.sql
```
Ví dụ cron (`crontab -e`) chạy 1h sáng mỗi ngày, giữ 14 ngày:
```cron
0 1 * * * mysqldump -u eng -p'mat-khau-manh' eng | gzip > /opt/backup/eng-$(date +\%F).sql.gz && find /opt/backup -name 'eng-*.sql.gz' -mtime +14 -delete
```

### 3.11. Cập nhật phiên bản mới
```bash
cd /opt/eng && sudo git pull
sudo .venv/bin/pip install -r web/requirements.txt
.venv/bin/python web/manage.py migrate
.venv/bin/python web/manage.py collectstatic --noinput
sudo systemctl restart eng
sudo docker compose up -d --build asr    # nếu service ASR có thay đổi
```

---

## Phụ lục — Sự cố thường gặp

| Triệu chứng | Nguyên nhân & cách xử lý |
|-------------|--------------------------|
| Trang hiện nhưng **mất CSS/JS** | Chưa `collectstatic`, hoặc dùng `CompressedManifestStaticFilesStorage` mà chưa gom static. Chạy lại `collectstatic --noinput`. |
| **Không có tiếng / ảnh không hiện** (audio, hình từ vựng 404) | Thiếu route media khi `DEBUG=False`. Kiểm tra [mục 0.3](#03-phục-vụ-file-media-audioảnhghi-âm) + thư mục `web/media/` có file không. |
| **Chấm phát âm không chạy** | Service ASR chưa bật hoặc sai `ASR_URL`. Kiểm tra `docker compose ps` (service `asr`), và `ASR_URL` trỏ đúng (`localhost:9002` khi web local — cổng publish của container, `asr:9000` khi web trong Docker). |
| Lỗi **400 Bad Request** | Thiếu host trong `ALLOWED_HOSTS`. Thêm IP/tên miền đang truy cập. |
| Lỗi **403 CSRF** khi bấm Lưu | Thiếu `CSRF_TRUSTED_ORIGINS` (phải đúng cả `http/https` và cổng). |
| `mysqlclient` cài lỗi (Windows) | Đã có wheel sẵn; nếu vẫn lỗi, dùng tạm `pip install pymysql` rồi thêm vào `web/config/__init__.py`: `import pymysql; pymysql.install_as_MySQLdb()`. |
| `database is locked` (SQLite) | Nhiều người ghi đồng thời — chuyển sang MySQL (Option 2/3). |
| Sai dấu tiếng Việt trong MySQL | DB phải `CHARACTER SET utf8mb4`. Tạo lại DB đúng charset rồi import lại. |
| Ghi âm của bé upload lỗi (413) | (Option 3) nginx chặn body lớn — thêm `client_max_body_size 25M;`. |

> ⚠️ Luôn để `web/.env`, `web/db.sqlite3`, `web/logs/`, `web/media/`, file bí mật của Docker **ngoài git** (đã có trong `.gitignore`).
