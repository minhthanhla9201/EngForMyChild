# Hướng dẫn triển khai TSM

Tài liệu hướng dẫn đưa ứng dụng TSM (Django 4.2) vào sử dụng thật theo 3 cách:

| Option | Phù hợp | CSDL | Độ phức tạp |
|--------|---------|------|-------------|
| **1. Local (SQLite3)** | 1 giáo viên dùng trên 1 máy (hoặc vài thiết bị trong LAN) | SQLite (1 file) | ⭐ Dễ nhất |
| **2. Docker** | Đóng gói chạy trên 1 server (Linux/NAS/VPS), dễ di chuyển | MySQL/MariaDB (trong container) | ⭐⭐ Trung bình |
| **3. Host thật + MySQL** | Nhiều người dùng, có tên miền + HTTPS | MySQL/MariaDB | ⭐⭐⭐ Cao |

> **Nguyên tắc chung cho mọi option** (KHÔNG bao giờ bỏ qua khi chạy thật):
> - `DEBUG=False`.
> - `SECRET_KEY` mới, ngẫu nhiên (không dùng key dev trong repo).
> - Khai báo đúng `ALLOWED_HOSTS` (và `CSRF_TRUSTED_ORIGINS` nếu truy cập qua IP/tên miền).
> - **Không dùng `runserver`** cho chạy thật — dùng `waitress` (Windows) hoặc `gunicorn` (Linux/Docker).
> - File tĩnh (CSS/JS) phục vụ qua **WhiteNoise** (khi `DEBUG=False`, Django không tự phục vụ static).
> - Đổi mật khẩu tài khoản `admin` mặc định.

---

## 0. Chuẩn bị chung (làm 1 lần cho cả 3 option)

### 0.1. Bổ sung thư viện

Thêm vào `requirements.txt`:
```
whitenoise>=6.6      # phục vụ file tĩnh khi DEBUG=False
waitress>=3.0        # WSGI server cho Windows (Option 1)
gunicorn>=21.2       # WSGI server cho Linux/Docker (Option 2, 3)
mysqlclient>=2.2     # driver MySQL (Option 2, 3)
```
> Option 1 (SQLite/Windows) chỉ cần `whitenoise` + `waitress`. Có thể để cả 4 dòng, chỉ cài cái cần.

### 0.2. Sửa `src/config/settings.py`

**a) Thêm WhiteNoise** vào `MIDDLEWARE`, ngay **sau** `SecurityMiddleware`:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # <-- THÊM DÒNG NÀY
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... giữ nguyên các dòng còn lại
]
```

**b) Nén & cache file tĩnh** — thêm vào khu vực `# ----- Tệp tĩnh -----`:
```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**c) Cho phép cấu hình CSRF qua biến môi trường** — thêm dưới phần đọc `ALLOWED_HOSTS`:
```python
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
```

> Ba thay đổi này an toàn cho cả môi trường dev (mặc định không bật gì thêm).

### 0.3. Sinh SECRET_KEY mới
```powershell
# Windows
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```
```bash
# Linux
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

---

## Option 1 — Local, SQLite3, cho 1 giáo viên

Đơn giản nhất: 1 file `db.sqlite3`, không cần cài CSDL server. Phù hợp 1 người dùng (hoặc vài thiết bị trong cùng wifi). Hướng dẫn này dành cho **máy tính hoàn toàn mới (chưa cài gì)**.

### 1.1. Cài đặt Python
1. Truy cập [python.org/downloads](https://www.python.org/downloads/) và tải bộ cài đặt Python mới nhất (vd: 3.11 hoặc 3.12).
2. Chạy file cài đặt, **BẮT BUỘC TICK VÀO Ô "Add python.exe to PATH"** (hoặc "Add Python to PATH") ở màn hình đầu tiên.
3. Bấm *Install Now* và đợi hoàn tất.
4. Mở ứng dụng **PowerShell**, gõ `python --version` để kiểm tra. Nếu hiện ra phiên bản Python là thành công.

### 1.2. Tải mã nguồn
1. Tải mã nguồn của TSM (có thể tải file `.zip` từ kho lưu trữ và giải nén, hoặc dùng `git clone`).
2. Đặt thư mục chứa mã nguồn ở một nơi dễ quản lý, ví dụ: `D:\TSM`.

### 1.3. Tạo môi trường ảo và cài đặt thư viện
Mở **PowerShell**, di chuyển tới thư mục chứa mã nguồn vừa giải nén:
```powershell
# Chuyển tới thư mục dự án (thay đường dẫn thực tế của bạn)
cd D:\TSM

# Tạo môi trường ảo (chỉ làm 1 lần)
python -m venv .venv

# Cài đặt thư viện cần thiết
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 1.4. Tạo `src/.env` cho chạy thật
Tạo một file có tên đúng là `.env` (không có đuôi .txt) bên trong thư mục `src`:
```ini
DEBUG=False
SECRET_KEY=dan-key-vua-sinh-o-buoc-0.3
# Chỉ máy này: 127.0.0.1,localhost
# Cho thiết bị khác trong LAN: thêm IP LAN của máy (vd 192.168.1.50)
ALLOWED_HOSTS=127.0.0.1,localhost,192.168.1.50
CSRF_TRUSTED_ORIGINS=http://192.168.1.50:9001
SESSION_COOKIE_AGE=3600
LOG_LEVEL=INFO
# Để trống DATABASE_URL = dùng SQLite (src/db.sqlite3)
```
> Tìm IP LAN: trong PowerShell gõ `ipconfig | Select-String "IPv4"`. Nên đặt **IP tĩnh** cho máy để IP không đổi sau khi khởi động lại máy hoặc router.

### 1.5. Tạo bảng + gom static + tài khoản
Vẫn trong **PowerShell** tại thư mục dự án (`D:\TSM`):
```powershell
.\.venv\Scripts\python.exe web\manage.py migrate
.\.venv\Scripts\python.exe web\manage.py collectstatic --noinput
.\.venv\Scripts\python.exe web\manage.py createsuperuser
.\.venv\Scripts\python.exe web\manage.py collectstatic
.\.venv\Scripts\python.exe web\manage.py check --deploy   # xem cảnh báo bảo mật
```

### 1.6. Mở firewall (nếu cho LAN truy cập) — PowerShell *Administrator*
Mở PowerShell bằng quyền Administrator (chuột phải > Run as Administrator) và chạy:
```powershell
New-NetFirewallRule -DisplayName "Eng Kid 9001" -Direction Inbound -LocalPort 9001 -Protocol TCP -Action Allow
```

### 1.7. Chạy server

Tạo file `start_tsm.bat` ở thư mục gốc dự án (`D:\TSM\start_tsm.bat`):
```bat
@echo off
REM Di chuyển vào thư mục web
cd /d "%~dp0web"
REM Chạy waitress từ môi trường ảo
..\.venv\Scripts\python.exe -m waitress --listen=0.0.0.0:9001 config.wsgi:application
```
Bấm đúp `start_tsm.bat` để chạy server (sẽ có 1 cửa sổ đen hiện ra, cần giữ nó luôn mở). 
**(Để dừng server: chỉ cần tắt cửa sổ đen này đi, hoặc bấm tổ hợp phím `Ctrl + C` bên trong cửa sổ)**

Truy cập ứng dụng:
- Trên máy chạy server: `http://127.0.0.1:9001`
- Thiết bị khác trong mạng LAN: `http://192.168.1.50:9001` (thay IP LAN của bạn)

### 1.8. Tự khởi động cùng Windows (tuỳ chọn)
- **Task Scheduler:** Mở Task Scheduler → Create Task → Triggers: *"At log on"* → Actions: chạy file `start_tsm.bat`. Tick *"Run whether user is logged on or not"* nếu muốn chạy nền.
- Hoặc dùng **NSSM** (chạy như Windows Service): `nssm install TSM` rồi cấu hình trỏ tới file `python.exe` trong `.venv` kèm các tham số của waitress.

### 1.9. 🔒 Sao lưu (BACKUP)

CSDL SQLite là **1 file duy nhất** `src/db.sqlite3` → sao lưu = chép file này sang chỗ an toàn.

**Cách A — chép file (đơn giản, khuyên dùng):**
Nên tắt server (đóng cửa sổ đen) vài giây, copy file `src/db.sqlite3` ra chỗ khác rồi bật lại. Hoặc dùng lệnh PowerShell:
```powershell
Copy-Item src\db.sqlite3 "D:\backup\tsm-$(Get-Date -Format yyyyMMdd-HHmm).sqlite3"
```

**Cách B — sao lưu logic (không cần tắt server, dạng JSON):**
```powershell
.\.venv\Scripts\python.exe src\manage.py dumpdata --natural-foreign --natural-primary `
  -e contenttypes -e auth.permission --indent 2 -o "D:\backup\tsm-$(Get-Date -Format yyyyMMdd).json"
```

**Cách C — tự động sao lưu lên GitHub Release** (script `backup_tsm.bat` dưới đây):

> ⚠️ **BẢO MẬT — đọc kỹ:** `db.sqlite3` chứa **thông tin cá nhân học sinh** (họ tên, SĐT), dữ liệu học phí **và hash mật khẩu tài khoản**. Cách này đẩy nguyên CSDL lên GitHub, nên **repo PHẢI luôn để chế độ private**. Nếu lỡ đổi repo sang *public*, **toàn bộ các bản backup cũ trong Releases sẽ bị lộ ngay lập tức**. An toàn hơn: dùng **một repo private RIÊNG cho backup** (tách khỏi repo mã nguồn), hoặc mã hoá file zip trước khi upload. Nếu chỉ cần đơn giản, **Cách A (chép file ra ổ khác / cloud)** là đủ và an toàn nhất.

Script tạo file `backup_tsm.bat` ở thư mục gốc dự án (tự dọn, chỉ giữ **14 bản** release gần nhất):
```bat
@echo off
setlocal

REM ==================================================
REM Chuyển vào thư mục src
REM ==================================================
cd /d "%~dp0src"

echo.
echo ==========================================
echo BAT DAU BACKUP SQLITE LEN GITHUB RELEASE
echo ==========================================
echo.

REM ==================================================
REM Tạo timestamp
REM Ví dụ:
REM backup-20260616-223015
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
REM Tạo thư mục backup
REM ==================================================
if not exist backup (
    mkdir backup
)

REM ==================================================
REM Tên file backup
REM ==================================================
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
REM Xóa zip cũ nếu tồn tại
REM ==================================================
if exist "%ZIP_FILE%" del /q "%ZIP_FILE%"

REM ==================================================
REM Nén database
REM ==================================================
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
    echo [ERROR] GitHub CLI chua dang nhap
    echo [INFO] Chay lenh: gh auth login

    del /q "%SQLITE_FILE%" 2>nul
    del /q "%ZIP_FILE%" 2>nul

    exit /b 1
)

REM ==================================================
REM Tạo GitHub Release
REM gh sẽ tự tạo tag nếu chưa tồn tại
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

## Cài đặt Github CLI
1. Tải và cài đặt
> https://cli.github.com/

2. Kiểm tra version
> gh --version

3. Đăng nhập
> gh auth login

→ Đặt Task Scheduler chạy file này hằng ngày (vd 23:00). Nên đồng bộ thư mục `D:\backup` lên cloud (OneDrive, Google Drive).

### 1.10. ♻️ Khôi phục (RESTORE)
1. **Tắt server** (đóng cửa sổ `start_tsm.bat`).
2. Chép bản sao an toàn đè lên file hiện tại:
   ```powershell
   Copy-Item "D:\backup\tsm-20260612.sqlite3" src\db.sqlite3 -Force
   ```
3. Bấm đúp `start_tsm.bat` chạy lại server.

> Khôi phục từ bản JSON (Cách B): Mở PowerShell, tạo DB trống mới (`migrate`) rồi chạy lệnh `.\.venv\Scripts\python.exe src\manage.py loaddata D:\backup\tsm-20260612.json`.

**Khôi phục từ GitHub Release (Cách C):**
1. Xem danh sách bản backup đã đẩy lên: `gh release list`
2. **Tắt server**, rồi tải bản cần khôi phục về thư mục `src` và giải nén:
   ```powershell
   cd src
   gh release download backup-20260616-223015        # thay bằng tag bản cần khôi phục
   Expand-Archive .\backup-20260616-223015.zip -DestinationPath . -Force
   Copy-Item .\backup.sqlite3 .\db.sqlite3 -Force     # file trong zip tên backup.sqlite3
   Remove-Item .\backup.sqlite3, .\backup-20260616-223015.zip
   ```
3. Bấm đúp `start_tsm.bat` chạy lại server.

---

## Option 2 — Docker (đóng gói, dễ di chuyển)

Đóng gói app + MariaDB thành các container, chạy bằng `docker compose`. Phù hợp khi triển khai lên 1 server Linux / NAS / VPS đã cài Docker.

### 2.1. Tạo `Dockerfile` ở thư mục gốc
```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# Thư viện hệ thống để build mysqlclient
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /app/src
# Gom file tĩnh ngay khi build (collectstatic không cần DB)
RUN python manage.py collectstatic --noinput

EXPOSE 9001
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:9001", "--workers", "3"]
```

### 2.2. Tạo `.dockerignore` ở thư mục gốc
```
.venv/
**/__pycache__/
src/db.sqlite3
src/logs/
src/staticfiles/
.git/
docs/
*.md
```

### 2.3. Tạo `docker-compose.yml` ở thư mục gốc
```yaml
services:
  db:
    image: mariadb:11
    environment:
      MARIADB_DATABASE: lsm
      MARIADB_USER: lsm_user
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
    build: .
    environment:
      DEBUG: "False"
      SECRET_KEY: ${SECRET_KEY}
      ALLOWED_HOSTS: ${ALLOWED_HOSTS}
      CSRF_TRUSTED_ORIGINS: ${CSRF_TRUSTED_ORIGINS}
      DATABASE_URL: mysql://lsm_user:${DB_PASSWORD}@db:3306/lsm
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "9001:9001"
    restart: unless-stopped

volumes:
  db_data:
```
> MariaDB 11 mặc định charset `utf8mb4` → tiếng Việt OK. `DATABASE_URL` trỏ host `db` (tên service), django-environ đọc trực tiếp từ biến môi trường nên **không cần file `.env` trong container**.

### 2.4. Tạo `.env` cho compose (cùng cấp `docker-compose.yml`)
```ini
SECRET_KEY=key-ngau-nhien-da-sinh
DB_PASSWORD=mat-khau-db-manh
DB_ROOT_PASSWORD=mat-khau-root-manh
ALLOWED_HOSTS=ten-mien-hoac-ip-server,localhost
CSRF_TRUSTED_ORIGINS=http://ip-server:9001
```
> ⚠️ Thêm `.env` và `docker-compose.yml` chứa bí mật vào `.gitignore`.

### 2.5. Khởi chạy
```bash
docker compose up -d --build              # build image + chạy nền
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```
Truy cập `http://<ip-server>:9001`. Xem log: `docker compose logs -f web`.

### 2.6. 🔒 Backup & ♻️ Restore (CSDL trong container)
```bash
# Backup
docker compose exec db sh -c 'exec mariadb-dump -u root -p"$MARIADB_ROOT_PASSWORD" lsm' > tsm-$(date +%F).sql

# Restore
cat tsm-2026-06-12.sql | docker compose exec -T db sh -c 'exec mariadb -u root -p"$MARIADB_ROOT_PASSWORD" lsm'
```
> Dữ liệu nằm trong volume `db_data` (vẫn còn khi container bị xoá). Nên thêm lệnh backup vào cron của server và đẩy file `.sql` ra nơi an toàn.

### 2.7. (Tuỳ chọn) HTTPS
Đặt một reverse proxy (nginx / Caddy / Traefik) phía trước container `web`, lo TLS. Caddy là gọn nhất (tự xin chứng chỉ Let's Encrypt). Khi đó `CSRF_TRUSTED_ORIGINS=https://ten-mien.com`.

---

## Option 3 — Host thật + MySQL (production, có HTTPS)

Triển khai trên server Linux thật (vd Ubuntu 22.04) với **MySQL/MariaDB + gunicorn + nginx + HTTPS**. Phù hợp nhiều người dùng, có tên miền.

### 3.1. Cài gói hệ thống
```bash
sudo apt update
sudo apt install -y python3-venv python3-dev build-essential pkg-config \
                    default-libmysqlclient-dev mariadb-server nginx git
```

### 3.2. Tạo CSDL (lưu ý `utf8mb4` cho tiếng Việt)
```bash
sudo mariadb
```
```sql
CREATE DATABASE lsm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lsm_user'@'localhost' IDENTIFIED BY 'mat-khau-manh';
GRANT ALL PRIVILEGES ON lsm.* TO 'lsm_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3.3. Lấy mã nguồn + môi trường ảo
```bash
cd /opt
sudo git clone <repo-url> tsm && cd tsm
sudo python3 -m venv .venv
sudo .venv/bin/pip install -r requirements.txt
```

### 3.4. Tạo `src/.env`
```ini
DEBUG=False
SECRET_KEY=key-ngau-nhien-da-sinh
ALLOWED_HOSTS=tsm.ten-mien.com
CSRF_TRUSTED_ORIGINS=https://tsm.ten-mien.com
DATABASE_URL=mysql://lsm_user:mat-khau-manh@127.0.0.1:3306/lsm
SESSION_COOKIE_AGE=3600
LOG_LEVEL=INFO
```

### 3.5. Khởi tạo dữ liệu + file tĩnh
```bash
.venv/bin/python src/manage.py migrate
.venv/bin/python src/manage.py collectstatic --noinput
.venv/bin/python src/manage.py createsuperuser
.venv/bin/python src/manage.py check --deploy
```

### 3.6. Chạy gunicorn như systemd service
Tạo `/etc/systemd/system/tsm.service`:
```ini
[Unit]
Description=TSM (Django) gunicorn
After=network.target mariadb.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/tsm/src
ExecStart=/opt/tsm/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:9001 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tsm
sudo systemctl status tsm
```

### 3.7. nginx reverse proxy + phục vụ static
Tạo `/etc/nginx/sites-available/tsm`:
```nginx
server {
    listen 80;
    server_name tsm.ten-mien.com;

    location /static/ {
        alias /opt/tsm/src/staticfiles/;
    }
    location / {
        proxy_pass http://127.0.0.1:9001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/tsm /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 3.8. Bật HTTPS (Let's Encrypt)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tsm.ten-mien.com
```
Certbot tự sửa nginx sang HTTPS + tự gia hạn. Đảm bảo `CSRF_TRUSTED_ORIGINS=https://tsm.ten-mien.com`.

### 3.9. 🔒 Backup & ♻️ Restore
```bash
# Backup (đặt vào cron hằng ngày)
mysqldump -u lsm_user -p lsm > /opt/backup/tsm-$(date +%F).sql

# Restore
mysql -u lsm_user -p lsm < /opt/backup/tsm-2026-06-12.sql
```
Ví dụ cron (mở bằng `crontab -e`) chạy 1h sáng mỗi ngày, giữ 14 ngày:
```cron
0 1 * * * mysqldump -u lsm_user -p'mat-khau-manh' lsm | gzip > /opt/backup/tsm-$(date +\%F).sql.gz && find /opt/backup -name 'tsm-*.sql.gz' -mtime +14 -delete
```

### 3.10. Cập nhật phiên bản mới
```bash
cd /opt/tsm && sudo git pull
sudo .venv/bin/pip install -r requirements.txt
.venv/bin/python src/manage.py migrate
.venv/bin/python src/manage.py collectstatic --noinput
sudo systemctl restart tsm
```

---

## Phụ lục — Sự cố thường gặp

| Triệu chứng | Nguyên nhân & cách xử lý |
|-------------|--------------------------|
| Trang hiện nhưng **mất CSS/JS** | Chưa cài WhiteNoise / chưa `collectstatic`. Kiểm tra mục [0.2](#02-sửa-srcconfigsettingspy) + chạy lại `collectstatic`. |
| Lỗi **400 Bad Request** | Thiếu host trong `ALLOWED_HOSTS`. Thêm IP/tên miền đang truy cập. |
| Lỗi **403 CSRF** khi bấm Lưu (điểm danh, đóng tiền…) | Thiếu `CSRF_TRUSTED_ORIGINS` (phải đúng cả `http/https` và cổng). |
| `mysqlclient` cài lỗi (Windows) | Đã có wheel sẵn; nếu vẫn lỗi, dùng tạm `pip install pymysql` rồi thêm vào `src/config/__init__.py`: `import pymysql; pymysql.install_as_MySQLdb()`. |
| `database is locked` (SQLite) | Nhiều người ghi đồng thời — chuyển sang MySQL (Option 2/3). |
| Sai dấu tiếng Việt trong MySQL | DB phải `CHARACTER SET utf8mb4`. Tạo lại DB đúng charset rồi import lại. |

> ⚠️ Luôn để `src/.env`, `db.sqlite3`, `src/logs/`, file bí mật của Docker **ngoài git** (đã có trong `.gitignore`).
