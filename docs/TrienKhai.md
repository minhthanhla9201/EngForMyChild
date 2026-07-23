# Hướng dẫn triển khai EngForMyChild

Hướng dẫn đưa ứng dụng EngForMyChild (Django) vào sử dụng thật theo 3 cách.

| Option | Phù hợp | CSDL | Độ phức tạp |
|--------|---------|------|-------------|
| **1. Local (SQLite) + ASR Docker** | 1 máy (hoặc LAN) | SQLite (1 file) | ⭐ Dễ |
| **2. Docker** | 1 server Linux/NAS/VPS | MariaDB (container) | ⭐⭐ TB |
| **3. Host thật + MySQL** | Nhiều người dùng, có HTTPS | MySQL/MariaDB | ⭐⭐⭐ Cao |

> **Kiến trúc:** 2 phần — **web** (`web/`, Django), **ASR** (`asr/`, faster-whisper trong Docker, cổng 9000). Web gọi ASR qua biến `ASR_URL`. TTS (edge-tts) và ghi âm sinh file trong `web/media/`.

> **Nguyên tắc chung (KHÔNG bỏ qua khi chạy thật):**
> - `DEBUG=False`, `SECRET_KEY` mới, `ALLOWED_HOSTS` + `CSRF_TRUSTED_ORIGINS` đúng.
> - Dùng **waitress** (Windows) hoặc **gunicorn** (Linux), không dùng `runserver`.
> - File tĩnh (CSS/JS) qua **WhiteNoise** → cần `collectstatic` trước.
> - File media (audio/ảnh/ghi âm) — xem [mục 0.3](#03-phục-vụ-file-media-audioảnhghi-âm). Dễ quên nhất: nếu không cấu hình, media **404** khi `DEBUG=False`.
> - Đổi mật khẩu admin mặc định.

---

## 0. Chuẩn bị chung (làm 1 lần cho cả 3 option)

### 0.1. Bổ sung thư viện

`web/requirements.txt` đã có `whitenoise` + `waitress`. Nếu triển khai Docker/Linux (Option 2, 3) thêm:
```
gunicorn>=21.2       # WSGI server cho Linux/Docker
mysqlclient>=2.2     # driver MySQL
```

### 0.2. WhiteNoise (đã cấu hình sẵn)

Đã có trong `web/config/settings.py`:
- `WhiteNoiseMiddleware` ngay sau `SecurityMiddleware` trong `MIDDLEWARE`.
- `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'` → **bắt buộc `collectstatic`** trước khi `DEBUG=False`.
- `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` đọc từ `.env` (cách nhau bằng dấu phẩy).

### 0.3. Phục vụ file media (audio/ảnh/ghi âm)

Media sinh lúc chạy (edge-tts, ghi âm) → **không dùng WhiteNoise** (chỉ quét 1 lần lúc khởi động). Django tự phục vụ qua `serve` view — đã cấu hình trong `web/config/urls.py` bằng `re_path` (hoạt động cả khi `DEBUG=False`).

> Cách này hợp Option 1 (local). Option 2/3 có nginx/Caddy thì để proxy phục vụ `/media/` nhanh hơn — xem mục tương ứng.

### 0.4. Sinh SECRET_KEY mới

```powershell
# Windows
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

```bash
# Linux
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

### 0.5. Sinh media (icon SVG + giọng tiếng Việt) — tham khảo

Các lệnh này **cần internet** (CDN emoji + edge-tts), **chạy sau `migrate`** (đọc từ vựng trong DB). Idempotent — file đã có thì bỏ qua. Lệnh cụ thể cho từng option nằm ở phần tương ứng.

| Lệnh | Sinh ra | Nếu KHÔNG chạy |
|------|---------|----------------|
| `fetch_images` | SVG hình minh hoạ từ vựng → `media/images/` | Từ vựng/game thiếu hình |
| `fetch_ui_icons` | SVG emoji giao diện → `media/images/` | Một số icon rơi về ký tự emoji |
| `gen_praise` | Giọng động viên/hướng dẫn tiếng Việt → `media/praise/` | Game/luyện thiếu giọng khen |
| `gen_vi_names --images-only` | Giọng đọc tên tiếng Việt của từ có ảnh → `media/names/` | **Game hình không đọc tên** (bé chưa biết chữ sẽ khó) |

> - Icon linh vật/huy hiệu/chủ đề dùng SVG **tĩnh** trong `web/static/icons/` (đã commit) → hiển thị đúng dù chưa chạy `fetch_ui_icons`; lệnh này chỉ bổ sung SVG cho emoji tĩnh khác.
> - Khi thêm **từ vựng mới**, chạy lại 4 lệnh trên để sinh hình + giọng cho từ mới.
> - Nếu deploy **offline hoàn toàn**: chạy 4 lệnh ở máy có mạng trước, chép `web/media/` sang máy đích.

---

## Option 1 — Local, SQLite3, cho 1 máy

Web chạy bằng `waitress`, ASR trong Docker. Phù hợp 1 người (hoặc LAN). Hướng dẫn cho **máy mới (chưa cài gì)**.

### 1.1. Cài đặt Python
1. Tải Python **3.14** từ [python.org/downloads](https://www.python.org/downloads/).
2. Chạy bộ cài, **tick "Add python.exe to PATH"**, bấm *Install Now*.
3. Kiểm tra: `python --version`.

### 1.2. Tải mã nguồn
Giải nén `.zip` hoặc `git clone` vào thư mục dễ quản lý, vd: `D:\EngForMyChild`.

### 1.3. Tạo môi trường ảo + cài thư viện

```powershell
cd D:\EngForMyChild
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r web\requirements.txt
```

### 1.4. Tạo `web/.env`

```ini
DEBUG=False
SECRET_KEY=key-vua-sinh-o-muc-0.4
ALLOWED_HOSTS=127.0.0.1,localhost        # thêm IP LAN nếu cho thiết bị khác truy cập
CSRF_TRUSTED_ORIGINS=http://localhost:9001,http://192.168.1.50:9001
ASR_URL=http://localhost:9002            # ASR trong Docker publish cổng 9002
SESSION_DAYS=30
LOG_LEVEL=INFO
# DATABASE_URL để trống → dùng SQLite (web/db.sqlite3)
```

> Tìm IP LAN: `ipconfig | Select-String "IPv4"`. Nên đặt **IP tĩnh** cho máy.

### 1.5. Khởi tạo dữ liệu

```powershell
# 1. Tạo bảng CSDL
.\.venv\Scripts\python.exe web\manage.py migrate

# 2. Sinh hình minh hoạ + giọng tiếng Việt (cần internet) — xem mục 0.5
.\.venv\Scripts\python.exe web\manage.py fetch_images
.\.venv\Scripts\python.exe web\manage.py fetch_ui_icons
.\.venv\Scripts\python.exe web\manage.py gen_praise
.\.venv\Scripts\python.exe web\manage.py gen_vi_names --images-only

# 3. Gom file tĩnh
.\.venv\Scripts\python.exe web\manage.py collectstatic --noinput

# 4. Tạo tài khoản admin
.\.venv\Scripts\python.exe web\manage.py createsuperuser

# 5. Kiểm tra bảo mật
.\.venv\Scripts\python.exe web\manage.py check --deploy
```

### 1.6. Chạy service ASR (Docker)

Cần cài **Docker Desktop** trước ([docker.com](https://www.docker.com/products/docker-desktop/)).

```powershell
docker compose up -d asr
```

> Lần đầu tải model Whisper (cache trong volume `asr_models`). Container nghe 9000, publish ra **9002** → khớp `ASR_URL=http://localhost:9002` ở bước 1.4. Có thể bỏ qua nếu chưa cần chấm phát âm — các phần khác vẫn chạy.

### 1.7. Mở firewall (nếu cho LAN truy cập)

Mở PowerShell **Administrator**:
```powershell
New-NetFirewallRule -DisplayName "EngForMyChild 9001" -Direction Inbound -LocalPort 9001 -Protocol TCP -Action Allow
```

### 1.8. Chạy server web

Tạo file `start_tsm.bat` ở thư mục gốc:
```bat
@echo off
cd /d "%~dp0web"
..\.venv\Scripts\python.exe -m waitress --listen=0.0.0.0:9001 config.wsgi:application
```
Bấm đúp để chạy (giữ cửa sổ luôn mở). Dừng: `Ctrl+C` hoặc tắt cửa sổ.

Truy cập:
- Máy chủ: `http://127.0.0.1:9001`
- Thiết bị trong LAN: `http://<IP-LAN>:9001`

> **Kiểm tra media:** mở bài từ vựng, bấm nghe. Nếu audio 404 → kiểm tra [mục 0.3](#03-phục-vụ-file-media-audioảnhghi-âm) và thư mục `web/media/audio/`.

### 1.9. Tự khởi động cùng Windows (tuỳ chọn)

- **Task Scheduler:** Trigger *"At log on"*, Action: chạy `start_tsm.bat`. Tick *"Run whether user is logged on or not"* nếu muốn chạy nền.
- **NSSM** (chạy như service): `nssm install EngForMyChild` trỏ tới `python.exe` trong `.venk` + tham số waitress.
- Docker Desktop nên đặt tự khởi động cùng Windows.

### 1.10. 🔒 Sao lưu & ♻️ Khôi phục

**CSDL** là 1 file `web/db.sqlite3` → sao lưu = copy file này:

```powershell
# Backup (tắt server vài giây trước khi copy)
Copy-Item web\db.sqlite3 "D:\backup\eng-$(Get-Date -Format yyyyMMdd-HHmm).sqlite3"

# Restore — chép đè, chạy lại server
Copy-Item "D:\backup\eng-20260612.sqlite3" web\db.sqlite3 -Force
```

**Backup logic (JSON, không cần tắt server):**
```powershell
.\.venv\Scripts\python.exe web\manage.py dumpdata --natural-foreign --natural-primary `
  -e contenttypes -e auth.permission --indent 2 -o "D:\backup\eng-$(Get-Date -Format yyyyMMdd).json"
# Restore từ JSON: migrate → loaddata
.\.venv\Scripts\python.exe web\manage.py loaddata D:\backup\eng-20260612.json
```

**Backup lên GitHub Release** (script `backup_tsm.bat` — tạo, gắn tag, upload + tự dọn giữ 14 bản):
> ⚠️ `db.sqlite3` chứa hash mật khẩu + dữ liệu bé. Repo **PHẢI private**. An toàn nhất: dùng cách A (copy).
> - Cài [GitHub CLI](https://cli.github.com/), đăng nhập: `gh auth login`
> - Đặt Task Scheduler chạy `backup_tsm.bat` hằng ngày.

**Khôi phục thư mục media (khi mất file nhưng DB còn):**
```powershell
.\.venv\Scripts\python.exe web\manage.py recreate_media     # audio phát âm + hướng dẫn
.\.venv\Scripts\python.exe web\manage.py fetch_images --force  # hình emoji (cần internet)
.\.venv\Scripts\python.exe web\manage.py gen_praise --force     # câu động viên (cần internet)
```

| Thư mục | Tạo lại? | Ghi chú |
|---|---|---|
| `media/audio/` | ✅ | edge-tts (giọng Neural). Mất mạng → dùng pyttsx3. |
| `media/instructions/` | ✅ | edge-tts giọng Việt. |
| `media/images/` | ✅ | Tải SVG từ CDN (cần internet). |
| `media/praise/` | ✅ | edge-tts giọng Việt (cần internet). |
| `media/recordings/` | ❌ | Giọng đọc của bé — DB chỉ lưu đường dẫn. Cần backup riêng. |

> Lần đầu có thể lâu (hàng trăm file). Dùng `--dry-run` để xem trước. Sau khi tạo xong, backup `web/media/` ngay.

---

## Option 2 — Docker (đóng gói, dễ di chuyển)

Web + MariaDB + ASR trong container, chạy bằng `docker compose`. Phù hợp server Linux/NAS/VPS.

### 2.1. Tạo `web/Dockerfile`

```dockerfile
FROM python:3.14-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn mysqlclient
COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

### 2.2. `.dockerignore` ở thư mục gốc

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
      ASR_URL: http://asr:9000          # gọi ASR qua tên service
    volumes:
      - media_data:/app/media
    depends_on:
      db: { condition: service_healthy }
      asr: { condition: service_started }
    ports:
      - "9001:8000"
    restart: unless-stopped

volumes:
  db_data:
  media_data:
```

> MariaDB 11 mặc định charset `utf8mb4`. Media dùng named volume để giữ qua rebuild.

### 2.4. Tạo `.env` (cùng cấp `docker-compose.yml`)

```ini
SECRET_KEY=key-ngau-nhien-da-sinh
DB_PASSWORD=mat-khau-db-manh
DB_ROOT_PASSWORD=mat-khau-root-manh
ALLOWED_HOSTS=ten-mien-hoac-ip-server,localhost
CSRF_TRUSTED_ORIGINS=http://ip-server:9001
```
> ⚠️ Thêm `.env` vào `.gitignore`.

### 2.5. Khởi chạy

```bash
docker compose up -d --build                                      # build + chạy nền
docker compose exec web python manage.py migrate                  # tạo bảng

# Sinh hình minh hoạ + giọng tiếng Việt (cần internet) — xem mục 0.5
docker compose exec web python manage.py fetch_images
docker compose exec web python manage.py fetch_ui_icons
docker compose exec web python manage.py gen_praise
docker compose exec web python manage.py gen_vi_names --images-only

docker compose exec web python manage.py createsuperuser          # tài khoản admin
docker compose exec web python manage.py check --deploy           # kiểm tra bảo mật
```

Truy cập `http://<ip-server>:9001`. Xem log: `docker compose logs -f web`.

### 2.6. 🔒 Backup & ♻️ Restore

```bash
# Backup CSDL
docker compose exec db sh -c 'exec mariadb-dump -u root -p"$MARIADB_ROOT_PASSWORD" eng' > eng-$(date +%F).sql

# Restore CSDL
cat eng-2026-06-12.sql | docker compose exec -T db sh -c 'exec mariadb -u root -p"$MARIADB_ROOT_PASSWORD" eng'

# Backup media
docker compose cp web:/app/media ./media-backup-$(date +%F)
```

> Nên thêm backup vào cron, đẩy file ra nơi an toàn.

### 2.7. (Tuỳ chọn) HTTPS + reverse proxy

Đặt nginx/Caddy/Traefik trước container `web`. Caddy gọn nhất (tự xin Let's Encrypt). Nên cho proxy phục vụ trực tiếp `/media/` (nhanh hơn Django) bằng cách mount `media_data` vào proxy. Đặt `CSRF_TRUSTED_ORIGINS=https://ten-mien.com`.

---

## Option 3 — Host thật + MySQL (production, có HTTPS)

Server Linux (vd Ubuntu 22.04) với MySQL/MariaDB + gunicorn + nginx + HTTPS. ASR trong Docker.

### 3.1. Cài gói hệ thống

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev build-essential pkg-config \
                    default-libmysqlclient-dev mariadb-server nginx git docker.io docker-compose-plugin
```

### 3.2. Tạo CSDL

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

### 3.4. Chạy service ASR

```bash
sudo docker compose up -d asr        # publish cổng 9000
```

### 3.5. Tạo `web/.env`

```ini
DEBUG=False
SECRET_KEY=key-ngau-nhien-da-sinh
ALLOWED_HOSTS=eng.ten-mien.com
CSRF_TRUSTED_ORIGINS=https://eng.ten-mien.com
DATABASE_URL=mysql://eng:mat-khau-manh@127.0.0.1:3306/eng
ASR_URL=http://localhost:9002
LOG_LEVEL=INFO
```

### 3.6. Khởi tạo dữ liệu

```bash
.venv/bin/python web/manage.py migrate
# Sinh hình minh hoạ + giọng tiếng Việt (cần internet) — xem mục 0.5
.venv/bin/python web/manage.py fetch_images
.venv/bin/python web/manage.py fetch_ui_icons
.venv/bin/python web/manage.py gen_praise
.venv/bin/python web/manage.py gen_vi_names --images-only
.venv/bin/python web/manage.py collectstatic --noinput
.venv/bin/python web/manage.py createsuperuser
.venv/bin/python web/manage.py check --deploy
```

### 3.7. Systemd service cho gunicorn

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
    location /media/ {
        alias /opt/eng/web/media/;          # nginx phục vụ nhanh hơn Django
    }
    location / {
        proxy_pass http://127.0.0.1:9001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 25M;           # cho phép ghi âm lớn
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/eng /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 3.9. HTTPS (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d eng.ten-mien.com
```

Certbot tự sửa nginx sang HTTPS + tự gia hạn. Đảm bảo `CSRF_TRUSTED_ORIGINS=https://eng.ten-mien.com`.

### 3.10. 🔒 Backup & ♻️ Restore

```bash
# Backup CSDL
mysqldump -u eng -p eng > /opt/backup/eng-$(date +%F).sql
# Restore
mysql -u eng -p eng < /opt/backup/eng-2026-06-12.sql

# Backup media
tar czf /opt/backup/media-$(date +%F).tar.gz -C /opt/eng/web media
```

**Cron hàng ngày (1h sáng, giữ 14 ngày):**
```cron
0 1 * * * mysqldump -u eng -p'mat-khau-manh' eng | gzip > /opt/backup/eng-$(date +\%F).sql.gz && find /opt/backup -name 'eng-*.sql.gz' -mtime +14 -delete
```

### 3.11. Cập nhật phiên bản mới

```bash
cd /opt/eng && sudo git pull
sudo .venv/bin/pip install -r web/requirements.txt
.venv/bin/python web/manage.py migrate
.venv/bin/python web/manage.py collectstatic --noinput
.venv/bin/python web/manage.py fetch_images          # sinh lại nếu thêm từ vựng/đổi icon
.venv/bin/python web/manage.py fetch_ui_icons
.venv/bin/python web/manage.py gen_vi_names --images-only
sudo systemctl restart eng
sudo docker compose up -d --build asr    # nếu ASR có thay đổi
```

---

## Phụ lục — Sự cố thường gặp

| Triệu chứng | Nguyên nhân & cách xử lý |
|-------------|--------------------------|
| Trang hiện nhưng **mất CSS/JS** | Chưa `collectstatic`. Chạy lại `collectstatic --noinput`. |
| **Không tiếng / ảnh 404** | Thiếu route media khi `DEBUG=False`. Kiểm tra [mục 0.3](#03-phục-vụ-file-media-audioảnhghi-âm) + thư mục `web/media/`. |
| **Game hình không đọc tên** khi bé chạm hình | Chưa sinh giọng. Chạy `gen_vi_names --images-only`; kiểm tra `media/names/name_*.mp3`. |
| **Icon rơi về emoji** | SVG tĩnh trong `web/static/icons/` đã lo; nếu vẫn lỗi → chưa `collectstatic`. Với emoji khác: chạy `fetch_ui_icons`. |
| **Chấm phát âm không chạy** | ASR chưa bật hoặc sai `ASR_URL`. Kiểm tra `docker compose ps` (service `asr`), và `ASR_URL` trỏ đúng. |
| Lỗi **400 Bad Request** | Thiếu host trong `ALLOWED_HOSTS`. |
| Lỗi **403 CSRF** khi lưu | Thiếu `CSRF_TRUSTED_ORIGINS` (phải đúng cả `http/https` và cổng). |
| `mysqlclient` lỗi (Windows) | Dùng tạm `pip install pymysql` rồi thêm vào `web/config/__init__.py`: `import pymysql; pymysql.install_as_MySQLdb()`. |
| `database is locked` (SQLite) | Nhiều người ghi đồng thời → chuyển MySQL (Option 2/3). |
| Sai dấu tiếng Việt (MySQL) | DB phải `CHARACTER SET utf8mb4`. Tạo lại đúng charset. |
| Upload ghi âm lỗi 413 | (Option 3) nginx chặn body lớn → thêm `client_max_body_size 25M;`. |

> ⚠️ Luôn để `web/.env`, `web/db.sqlite3`, `web/logs/`, `web/media/`, file bí mật Docker **ngoài git** (đã có trong `.gitignore`).
