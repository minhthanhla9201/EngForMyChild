# Thiết kế cơ bản — EngForMyChild

> Tài liệu **thiết kế cơ bản** (basic design) cho website học tiếng Anh cho bé 6–7 tuổi, chạy **local**.
> Mục đích: giúp người bảo trì nắm nhanh **cấu trúc project**, **chức năng đã làm theo từng mục**, và **luồng xử lý** để dễ sửa/mở rộng.
>
> Cập nhật: 2026-07-02. Tài liệu liên quan: [YeuCau.md](YeuCau.md) (yêu cầu), [ThietKeDuLieu.md](ThietKeDuLieu.md) (mô hình dữ liệu chi tiết), [CongNghe.md](CongNghe.md) (công nghệ).

---

## 1. Tổng quan hệ thống

| Hạng mục | Nội dung |
|---|---|
| **Mục tiêu** | Bé học tiếng Anh: phát âm → từ vựng → ngữ pháp, qua trò chơi. Giao diện Việt + Anh. |
| **Đối tượng** | Bé 6–7 tuổi (khu của bé) + phụ huynh (khu quản lý). |
| **Kiểu triển khai** | Chạy **local** trên máy nhà (không cần server ngoài). Chạy trực tiếp Python hoặc Docker. |
| **Backend** | Django (Python) — 5 app nội bộ. |
| **Frontend** | Bootstrap + Bootstrap Icons + HTMX + Alpine.js (tải sẵn `static/vendor/`, **không CDN** → chạy offline). |
| **CSDL** | SQLite (mặc định) → có thể đổi MySQL chỉ qua `DATABASE_URL` trong `.env`, **không sửa code**. |
| **TTS (đọc mẫu)** | edge-tts (cần mạng) → dự phòng pyttsx3 (offline). |
| **ASR (chấm giọng)** | faster-whisper — **GĐ 3, chưa làm**. |

### Kiến trúc 2 khu (một lần đăng nhập)

```
                 ┌─────────────────────────────────────────────┐
   Đăng nhập ──▶ │  🧒 KHU CỦA BÉ  (navbar xanh, base_kid)      │
   (phụ huynh)   │  /  /learn/  /speak/  /games/                │
                 │  → chỉ cần @login_required                   │
                 └───────────────┬─────────────────────────────┘
                                 │  bấm "Cho phụ huynh" + nhập passcode
                                 ▼
                 ┌─────────────────────────────────────────────┐
                 │  ⚙️ KHU QUẢN LÝ (navbar xám, base_manage)    │
                 │  /manage/...  /admin/                        │
                 │  → @manage_required (login + passcode 30')   │
                 └─────────────────────────────────────────────┘
```

- **Lớp khoá 1:** đăng nhập Django (tài khoản phụ huynh). Phiên sống 30 ngày, trượt hạn.
- **Lớp khoá 2:** passcode 4–6 số cho khu quản lý — để bé không tự vào nghịch. Mở khoá giữ 30 phút không thao tác (trượt hạn), bấm "Về khu của bé" để khoá ngay.

---

## 2. Cấu trúc thư mục

```
EngForMyChild/
├─ README.md                 # Hướng dẫn cài & chạy (cho người không rành lập trình)
├─ docker-compose.yml        # Chạy bằng Docker (kèm chỗ bật MySQL/ASR sau)
├─ docs/                     # Tài liệu dự án
│  ├─ YeuCau.md              #   Yêu cầu, đối tượng, lộ trình các giai đoạn
│  ├─ ThietKeDuLieu.md       #   Mô hình dữ liệu + ERD + tương thích SQLite/MySQL
│  ├─ ThietKeCoBan.md        #   ★ Tài liệu này
│  └─ CongNghe.md            #   Công nghệ sử dụng
├─ wireframe/                # Xem trước bố cục khu quản lý KHÔNG cần chạy server
└─ web/                      # Mã nguồn Django
   ├─ manage.py
   ├─ .env / .env.example    # Cấu hình theo máy (DEBUG, DATABASE_URL, TTS_VOICE...)
   ├─ db.sqlite3             # CSDL SQLite
   ├─ sample_words.csv       # File từ vựng mẫu nhỏ (thử định dạng)
   ├─ words_backup.csv       # Bộ từ vựng đầy đủ (~430 từ / 28 chủ đề) — nhập/restore

   ├─ config/                # ⚙️ Cấu hình dự án
   │  ├─ settings.py         #   Toàn bộ cấu hình (đọc .env)
   │  ├─ urls.py             #   Định tuyến gốc (map các khu)
   │  └─ logging_utils.py    #   Handler ghi log ra file theo ngày
   ├─ core/                  # 🧩 Dùng chung (không có URL riêng)
   │  ├─ models.py           #   AuditedModel, YesNo
   │  ├─ middleware.py       #   CurrentUserMiddleware (lấy user hiện tại)
   │  └─ decorators.py       #   manage_required (khoá passcode)
   ├─ accounts/              # 👤 Tài khoản, hồ sơ bé, passcode, trang chủ bé, tiến độ
   ├─ catalog/               # 📚 Nội dung học: chủ đề, từ vựng, audio, nhập CSV
   │  ├─ audio.py / tts.py / ipa.py     # service sinh audio, TTS, phiên âm IPA
   │  ├─ imports.py                     # service nhập/xuất CSV (dùng chung web + CLI)
   │  ├─ emoji_map.py                   # bảng map từ → emoji để tự tải hình minh hoạ
   │  ├─ urls.py / urls_manage.py       # URL khu bé / khu quản lý
   │  └─ management/commands/           # import_words, export_words, fetch_images
   ├─ pronunciation/         # 🎤 Luyện phát âm (ghi âm) → Attempt
   ├─ games/                 # 🎮 Trò chơi
   │  └─ engine/             #   Luật chơi tách theo module (listen_pick, match_pairs...)
   ├─ templates/             # Giao diện (base + base_kid + base_manage + theo app)
   ├─ static/                # CSS + vendor libs (Bootstrap/HTMX/Alpine — offline)
   ├─ media/                 # File sinh ra: audio/ (TTS), images/ (hình từ), recordings/ (giọng bé)
   └─ logs/                  # Log theo ngày: app-*, error-*, security-*
```

### Vai trò 5 app Django

| App | Trách nhiệm | Phụ thuộc |
|---|---|---|
| **core** | Nền tảng dùng chung: base model audit, cờ Y/N, middleware user hiện tại, decorator khoá passcode. Không có model bảng riêng, không có URL. | — |
| **accounts** | Đăng nhập, hồ sơ bé (`ChildProfile`), passcode khu quản lý (`ManagePasscode`), trang chủ khu bé, dashboard, trang tiến độ. | core, catalog, games, pronunciation |
| **catalog** | Kho nội dung học **dùng chung** cho mọi bé: `Topic` → `Word` → `AudioClip`. Sinh IPA, sinh + cache audio TTS, nhập CSV. | core |
| **pronunciation** | Luyện phát âm: bé thu giọng đọc 1 từ → lưu `Attempt`. Chấm điểm để trống (GĐ 3). | core, catalog, accounts |
| **games** | Trò chơi theo kiến trúc "khuôn + dữ liệu": `GameType` (cấu hình) + `GameResult` (kết quả) + `engine/` (luật chơi). | core, catalog, accounts |

---

## 3. Mô hình dữ liệu (tóm tắt)

> Chi tiết đầy đủ + ERD: [ThietKeDuLieu.md](ThietKeDuLieu.md). Dưới đây là bản rút gọn để bảo trì nhanh.

```
User (Django auth)
  └─(owner)─▶ ChildProfile ──┬─▶ Attempt ───▶ Word
                             └─▶ GameResult ─▶ GameType
                                            └─▶ Topic

Topic ─▶ Word ─▶ AudioClip
ManagePasscode (singleton pk=1)
```

**Quy ước chung (mọi bảng nghiệp vụ):**
- Kế thừa **`AuditedModel`** ([core/models.py](../web/core/models.py)) → tự có `created_at`, `updated_at`, `created_by`, `updated_by`. `created_by/updated_by` **tự điền** từ user đăng nhập (qua `CurrentUserMiddleware`) — không gán tay ở view.
- Cờ bật/tắt dùng **`YesNo`** (CharField `'Y'/'N'`), **không** dùng `BooleanField` → bằng nhau trên SQLite & MySQL. So sánh luôn `== 'Y'` (chuỗi `'N'` vẫn truthy).

| Model | App | Ý nghĩa | Điểm cần nhớ |
|---|---|---|---|
| **ChildProfile** | accounts | Hồ sơ 1 bé, thuộc 1 phụ huynh (`owner`) | Mọi dữ liệu của bé gắn qua đây, **không** gắn thẳng owner. |
| **ManagePasscode** | accounts | Passcode khu quản lý (singleton pk=1) | Lưu **hash**, không lưu mã thô. `get_solo()`, `set_passcode()`, `check_passcode()`. |
| **Topic** | catalog | Chủ đề từ vựng | `slug` unique; kho dùng chung, **không** lọc theo owner. |
| **Word** | catalog | 1 từ vựng thuộc chủ đề | Unique `(topic, text_en)` → import CSV idempotent. `phonetic` (IPA) tự sinh khi trống. |
| **AudioClip** | catalog | Audio phát âm 1 từ (nhiều clip/từ) | Nguồn `tts`/`recorded`; ưu tiên recorded/default. File `media/audio/word_<id>.mp3`. |
| **Attempt** | pronunciation | 1 lần bé thu giọng đọc 1 từ | `recording` là file; `asr_text/score/stars` để trống → GĐ 3 điền. |
| **GameType** | games | Cấu hình 1 loại game | `module` trỏ file trong `engine/`; `min_words`, `needs_image`, `needs_asr`. Bật/tắt bằng DB. |
| **GameResult** | games | Kết quả 1 ván chơi của bé | `stars/score/total/duration_sec`. |

---

## 4. Bản đồ định tuyến (URL)

Định tuyến gốc: [config/urls.py](../web/config/urls.py).

| Tiền tố | App / file | Khu | Bảo vệ |
|---|---|---|---|
| `/` | accounts | Trang chủ bé, đăng nhập/xuất | login |
| `/learn/` | catalog `urls.py` | Học từ vựng, nghe mẫu | login |
| `/speak/` | pronunciation | Luyện phát âm | login |
| `/games/` | games | Trò chơi | login |
| `/manage/` | accounts + catalog `urls_manage.py` | Khu quản lý | **login + passcode** |
| `/admin/` | Django Admin | Quản trị sâu | superuser |

### Chi tiết URL chính

**accounts** ([urls.py](../web/accounts/urls.py))
| URL | View | Chức năng |
|---|---|---|
| `/` | `home` | Trang chủ khu của bé (3 hoạt động lớn) |
| `/login/` `/logout/` | `ParentLoginView` / Django | Đăng nhập (ghi log lỗi) / đăng xuất |
| `/manage/unlock/` | `manage_unlock` | Nhập/đặt passcode để mở khoá khu quản lý |
| `/manage/lock/` | `manage_lock` | Khoá lại, về khu của bé |
| `/manage/passcode/change/` | `manage_passcode_change` | Đổi passcode |
| `/manage/` | `dashboard` | Bảng điều khiển (số liệu + hồ sơ bé) |
| `/manage/children/add/` `.../edit/` | `child_add` / `child_edit` | Thêm / sửa hồ sơ bé |
| `/manage/children/<pk>/delete/` | `child_delete` | Xoá bé + toàn bộ dữ liệu liên quan (POST, xác nhận tên) |
| `/manage/progress/` | `progress` | Tiến độ (kết quả chơi + lần luyện) |

**catalog — khu bé** ([urls.py](../web/catalog/urls.py)): `/learn/` (chủ đề), `/learn/topic/<slug>/` (từ), `/learn/word/<pk>/audio/` (lấy URL audio, JSON).
**catalog — khu quản lý** ([urls_manage.py](../web/catalog/urls_manage.py)): `/manage/topics/`, `.../add|edit`, `/manage/words/`, `.../add|edit`, `/manage/import/` (nhập CSV), `/manage/export/` (xuất CSV backup → `word_export`).
**pronunciation** ([urls.py](../web/pronunciation/urls.py)): `/speak/` (chọn), `/speak/<child>/<slug>/` (luyện), `/speak/<child>/word/<word>/save/` (POST bản ghi).
**games** ([urls.py](../web/games/urls.py)): `/games/` (chọn), `/games/<child>/<code>/<slug>/` (chơi), `.../submit/` (POST kết quả).

---

## 5. Chức năng đã làm — theo từng mục

### 5.0. Nền tảng dùng chung (app `core`) — GĐ 0
- **AuditedModel** — base cho mọi bảng: 4 cột audit, tự điền người tạo/sửa.
- **YesNo** — cờ Y/N thống nhất SQLite↔MySQL.
- **CurrentUserMiddleware** ([middleware.py](../web/core/middleware.py)) — lưu user request vào thread-local để model tự điền audit, giữ view mỏng.
- **manage_required** ([decorators.py](../web/core/decorators.py)) — chặn khu quản lý: cần login + đã mở khoá passcode còn hạn; thiếu → chuyển tới màn nhập passcode kèm `?next`; qua được thì trượt hạn.
- **Logging** ([config/logging_utils.py](../web/config/logging_utils.py), cấu hình trong settings) — ghi `app-*`, `error-*`, `security-*` theo ngày, giữ 30 ngày. Logger nội bộ: `logging.getLogger('eng.<phần>')`.

### 5.1. Tài khoản & khu quản lý (app `accounts`) — GĐ 0
- **Đăng nhập** — dùng view Django, ghi log lý do lỗi để chẩn đoán ("sai mật khẩu"...). Phiên 30 ngày trượt hạn.
- **Passcode khu quản lý** — lần đầu chưa có → buộc **đặt** (4–6 số); sau đó **nhập** để mở khoá 30 phút; **đổi** passcode phải nhập đúng mã cũ; **khoá lại** ngay. Lưu hash.
- **Hồ sơ bé (CRUD)** — thêm/sửa/**xoá** bé; `owner` luôn gán theo phụ huynh đăng nhập; sửa/xoá/xem lọc theo owner (404 nếu của người khác).
  - **Xoá bé (xoá cứng có chủ đích):** nút "Xoá bé" chỉ hiện ở màn **sửa** → modal xác nhận, phải **gõ đúng tên bé** mới xoá (chống nhầm). Chỉ nhận **POST**. Xoá kéo theo **toàn bộ dữ liệu của bé**: `Attempt` + `GameResult` tự xoá theo (`on_delete=CASCADE`), và **file ghi âm** trong `media/recordings/` được **dọn tay** trước khi xoá bản ghi (Django không tự xoá file). Đây là ngoại lệ có chủ đích so với quy ước "xoá mềm" chung — hợp lý cho app local trong gia đình.
- **Bảng điều khiển** — số bé / chủ đề / từ đang dùng + lối tắt + danh sách bé.
- **Trang tiến độ** — gộp `GameResult` + `Attempt` của các bé thuộc phụ huynh; lọc theo 1 bé qua `?child=<pk>`; tổng sao / số ván / số lần luyện.

### 5.2. Nội dung học & nghe mẫu (app `catalog`) — GĐ 1
- **Xem học (khu bé)** — danh sách chủ đề → danh sách từ (kèm nút 🔊 Nghe).
- **Nghe phát âm** — `word_audio` trả URL audio (JSON). Cơ chế **sinh + cache**: [audio.py](../web/catalog/audio.py) `get_clip()` ưu tiên clip đã có; chưa có thì gọi TTS, lưu `media/audio/word_<id>.mp3`, tạo `AudioClip`. Lần sau phát ngay.
- **TTS 2 tầng dự phòng** ([tts.py](../web/catalog/tts.py)) — thử **edge-tts** (cần mạng, giọng hay) → lỗi thì **pyttsx3** (offline) → cả hai lỗi trả `None` (view báo nhẹ, không 500).
- **Sinh IPA** ([ipa.py](../web/catalog/ipa.py)) — tự điền `phonetic` khi để trống.
- **Quản lý nội dung (khu quản lý)** — CRUD chủ đề (slug tự sinh), CRUD từ vựng (lọc theo chủ đề + tìm `?q=` + phân trang), **nhập CSV**.
- **Nhập CSV — service dùng chung** ([imports.py](../web/catalog/imports.py)) — dùng cho cả web lẫn lệnh `import_words`. **Idempotent** (chạy lại không trùng nhờ unique `(topic,text_en)`), tự tạo chủ đề, tự sinh IPA, tuỳ chọn sinh audio (`--no-audio` để bỏ khi offline). Trả dict thống kê.
- **Xuất CSV (backup/restore)** ([imports.py](../web/catalog/imports.py) `export_words()` + view `word_export`) — nút **Xuất CSV** ở màn quản lý từ vựng & màn Nhập CSV tải toàn bộ từ ra file `words_backup.csv`. **Cột xuất khớp đúng cột nhập** (`topic, topic_vi, text_en, text_vi, phonetic, level, image`, kèm BOM cho Excel) → **upload lại chính file này để khôi phục** (idempotent, không tạo trùng). Có lệnh CLI đối xứng `export_words [path]`. Lưu ý: import bỏ qua cột `phonetic` (tự sinh khi trống) — cột này chỉ để backup đầy đủ/đọc bằng Excel.
- **Cột `image` trong CSV** — là **đường dẫn file hình trong media** (vd `images/cat.jpg`), không phải ảnh nhúng. Import chỉ **lưu tham chiếu** (không copy/tải file) → file hình phải tự đặt sẵn trong `media/images/`. Nhập lại có giá trị mới sẽ **cập nhật** đường dẫn hình (giống `text_vi`). Hình vẫn có thể upload tay ở màn sửa từ như trước.
- **Hình minh hoạ tự động** ([emoji_map.py](../web/catalog/emoji_map.py) + lệnh `fetch_images`) — map mỗi `text_en` → emoji phù hợp, tải **SVG** về `media/images/` **một lần** rồi gán vào `Word.image`. Sau đó **học offline** (file đã ở máy). Lệnh idempotent; `--force` gán lại tất cả, `--offline` chỉ dùng SVG có sẵn, `--words a,b,c` chỉ áp cho từ chỉ định. Bộ dữ liệu hiện gán hình cho ~99% từ (còn lại là số ≥11 — emoji không có).
  - **Hai bộ hình** qua `--style`: `twemoji` (mặc định, khối màu đầy, CC-BY 4.0) lưu `images/`; `openmoji` (vẽ tay, nét mảnh, CC BY-SA 4.0) lưu `images/openmoji/` — hai bộ tách thư mục nên không đè nhau. Hiện ~33 từ tiêu biểu đã đổi sang OpenMoji.
  - **Thứ tự ưu tiên hiển thị:** ảnh upload tay > emoji SVG (Twemoji/OpenMoji) > icon 🔤 tạm.

### 5.3. Luyện phát âm (app `pronunciation`) — GĐ 2
- **Luồng:** chọn bé + chủ đề → màn luyện hiện từng từ → bé **Nghe mẫu** (dùng lại API audio catalog) → **Thu giọng** (MediaRecorder trình duyệt) → POST multipart → lưu `Attempt` → từ kế tiếp.
- Client dùng **Alpine.js**; danh sách từ truyền qua `json_script` (không `json.dumps` phía view → tránh mã hoá 2 lần).
- **Chưa chấm điểm** — `save_attempt` chỉ lưu bản ghi + trả thông điệp khích lệ. `asr_text/score/stars` để trống chờ **GĐ 3**.
- Kiểm owner: chỉ luyện trên hồ sơ bé của chính phụ huynh.

### 5.4. Trò chơi (app `games`) — GĐ 4
- **Kiến trúc "khuôn + dữ liệu":** luật chơi nằm trong module Python [engine/](../web/games/engine/), cấu hình nằm trong DB (`GameType`). **Thêm game mới = thêm 1 file module + 1 bản ghi GameType**, không sửa view/màn chọn game.
- **Interface mỗi module** ([engine/base.py](../web/games/engine/base.py)): `build_round(words)` → dữ liệu 1 vòng; `score_round(payload)` → `{score, total, stars}`. Quy đổi sao dùng chung `stars_from_ratio` (≥90%→3⭐, ≥70%→2⭐, ≥40%→1⭐).
- **Nạp module an toàn** ([engine/registry.py](../web/games/engine/registry.py)) — `load_game_module()` chỉ nạp trong package `games.engine`, kiểm tên hợp lệ + đủ 2 hàm → tránh import tuỳ tiện từ DB.
- **Luồng chơi:** chọn bé + chủ đề + game → `play` dựng vòng (kiểm đủ `min_words`, nếu game `needs_image` thì lọc từ có hình) → render `play_<module>.html` → client chơi → `submit` chấm + lưu `GameResult` + trả sao.
- **2 game hiện có:** *Nghe & chọn* 👂 (`listen_pick`), *Lật thẻ tìm cặp* 🃏 (`match_pairs`).

---

## 6. Giao diện (templates)

- **Kế thừa:** `base.html` (khung chung: nạp vendor CSS/JS) → `base_kid.html` (khu bé, navbar xanh) & `base_manage.html` (khu quản lý, navbar xám).
- **Offline:** mọi thư viện nạp từ `static/vendor/` — **không** gọi CDN.
- **Tương tác nhẹ:** HTMX (partial) + Alpine.js (state phía client cho luyện phát âm & game). Dữ liệu từ server → client qua `{{ ...|json_script }}` (an toàn, tránh mã hoá 2 lần).
- **Wireframe** ([wireframe/](../wireframe/)) — bản HTML tĩnh xem trước 6 màn quản lý, dùng CSS thật, **không cần chạy server**; đồng bộ khi đổi `style.css` theo `wireframe/README.md`.

Nhóm template theo app: `templates/accounts/`, `catalog/` (+ `catalog/manage/`), `pronunciation/`, `games/`.

---

## 7. Cấu hình & vận hành

- **Cấu hình theo máy:** `web/.env` (mẫu `.env.example`). Mục quan trọng: `DEBUG`, `DATABASE_URL`, `SESSION_DAYS`, `MANAGE_UNLOCK_MINUTES`, `TTS_VOICE`, `ASR_URL`, `LOG_LEVEL`.
- **Đổi giọng đọc mẫu:** sửa `TTS_VOICE` trong `.env` → khởi động lại server → xoá audio cũ (`media/audio/*.mp3` + `AudioClip` trong Admin) để sinh lại bằng giọng mới. Hướng dẫn chi tiết + danh sách giọng: [README.md](../README.md) mục "Đổi giọng đọc".
- **Đổi CSDL SQLite ↔ MySQL:** chỉ sửa `DATABASE_URL`, không sửa code (settings đọc qua `dj_database_url`). File SQLite neo tuyệt đối vào `web/` để tránh lệch DB theo thư mục chạy lệnh.
- **Media** (`media/audio|images|recordings/`) và **DB** giữ qua các lần chạy; khi dùng Docker gắn volume.
- **Chạy:** `.\.venv\Scripts\python.exe web\manage.py runserver` → http://127.0.0.1:8000 (đăng nhập `admin`). Chi tiết & cheat-sheet: [README.md](../README.md).

---

## 8. Trạng thái & việc còn lại

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| GĐ 0 | Khung + đăng nhập + hồ sơ bé + passcode | ✅ Xong |
| GĐ 1 | Từ vựng + nhập CSV + nghe mẫu (TTS/IPA) | ✅ Xong |
| GĐ 2 | Luyện phát âm + ghi âm | ✅ Xong (chưa chấm điểm) |
| GĐ 4 | Trò chơi (Nghe & chọn, Lật thẻ) + sao | ✅ Xong |
| **GĐ 3** | **Chấm điểm phát âm bằng faster-whisper** (điền `asr_text/score/stars` của `Attempt`; cần Docker) | ⏳ Chưa |
| **GĐ 5** | **Ngữ pháp + huy hiệu + trang tiến độ phụ huynh nâng cao** | ⏳ Chưa |

**Điểm mở rộng đã chuẩn bị sẵn (dễ nối GĐ sau):**
- Cột chấm điểm trong `Attempt` + `ASR_URL` trong settings → sẵn cho GĐ 3.
- `GameType.needs_asr` → game dùng chấm giọng ở GĐ sau.
- Kiến trúc engine game → thêm game không đụng view.
- Service TTS/IPA/import tách riêng → thay/nâng cấp cục bộ, có thể mock trong test.

---

## 9. Nguyên tắc bảo trì (rút gọn từ skill `eng-coding`)

1. Bảng nghiệp vụ **kế thừa `AuditedModel`**, không khai lại cột audit, không gán `created_by/updated_by` tay.
2. Cờ bật/tắt dùng **`YesNo`** (`'Y'/'N'`), so sánh `== 'Y'`. Không dùng `BooleanField`.
3. Chuỗi tìm kiếm dùng `__icontains` (nhất quán hoa-thường 2 loại DB). Cột unique/index giữ `max_length ≤ 191`.
4. View **mỏng**: logic nghiệp vụ (TTS, import, luật game) đặt trong service/engine để tái dùng cho cả web lẫn CLI và dễ test.
5. Dữ liệu server → client qua `json_script`, **không** `json.dumps` ở view.
6. Khu quản lý luôn `@manage_required`; dữ liệu của bé luôn **lọc theo owner**.
7. Nội dung học (`Topic/Word/AudioClip`) là **kho dùng chung** — không lọc owner.
8. Không gọi TTS trực tiếp — luôn qua `catalog.audio.get_clip()` (để tận dụng cache).

---

## 10. Map wireframe ↔ chức năng ↔ màn thật

Wireframe ([wireframe/](../wireframe/), mở [index.html](../wireframe/index.html)) là bản HTML tĩnh xem trước bố cục — **không chạy logic**, các màn động hiển thị ở một trạng thái đại diện. Bảng dưới nối **từng file wireframe** với **chức năng** (mục 5), **URL/view** thật, và **template** thật để khi sửa giao diện biết chỗ nào ăn với chỗ nào.

### 🔑 Đăng nhập
| Wireframe | Chức năng (mục) | URL → View | Template thật |
|---|---|---|---|
| [login.html](../wireframe/login.html) | Đăng nhập phụ huynh (5.1) | `/login/` → `ParentLoginView` | `accounts/login.html` |

### 🧒 Khu của bé (navbar xanh, `base_kid.html`)
| Wireframe | Chức năng (mục) | URL → View | Template thật |
|---|---|---|---|
| *(mục lục không có thẻ riêng)* | Trang chủ bé — 3 hoạt động (5.1) | `/` → `home` | `accounts/kid_home.html` |
| [learn-topics.html](../wireframe/learn-topics.html) | Học: chọn chủ đề (5.2) | `/learn/` → `topic_list` | `catalog/topic_list.html` |
| [learn-words.html](../wireframe/learn-words.html) | Học: từ trong chủ đề + 🔊 Nghe (5.2) | `/learn/topic/<slug>/` → `word_list` (+ `/learn/word/<pk>/audio/` → `word_audio`) | `catalog/word_list.html` |
| [speak-choose.html](../wireframe/speak-choose.html) | Phát âm: chọn bé & chủ đề (5.3) | `/speak/` → `choose` | `pronunciation/choose.html` |
| [speak-practice.html](../wireframe/speak-practice.html) | Phát âm: đọc theo & ghi âm (5.3) | `/speak/<child>/<slug>/` → `practice` (+ `.../word/<word>/save/` → `save_attempt`) | `pronunciation/practice.html` |
| [game-choose.html](../wireframe/game-choose.html) | Trò chơi: chọn bé/game/chủ đề (5.4) | `/games/` → `choose` | `games/choose.html` |
| [game-listen.html](../wireframe/game-listen.html) | Game *Nghe & chọn* 👂 (5.4) | `/games/<child>/<code>/<slug>/` → `play` (module `listen_pick`) | `games/play_listen_pick.html` |
| [game-match.html](../wireframe/game-match.html) | Game *Lật thẻ tìm cặp* 🃏 + kết quả ⭐ (5.4) | `/games/<child>/<code>/<slug>/` → `play` (module `match_pairs`) | `games/play_match_pairs.html` |
| [game-empty.html](../wireframe/game-empty.html) | Trạng thái chủ đề chưa đủ từ (5.4) | nhánh của `play` khi `words < min_words` | `games/play_empty.html` |

### 🔒 Vào khu quản lý — passcode
| Wireframe | Chức năng (mục) | URL → View | Template thật |
|---|---|---|---|
| [pass-enter.html](../wireframe/pass-enter.html) | Nhập passcode mở khoá (5.0/5.1) | `/manage/unlock/` → `manage_unlock` (đã đặt) | `accounts/manage_unlock.html` |
| [pass-set.html](../wireframe/pass-set.html) | Đặt passcode lần đầu (5.1) | `/manage/unlock/` → `manage_unlock` (chưa đặt) | `accounts/manage_set_passcode.html` |
| [pass-change.html](../wireframe/pass-change.html) | Đổi passcode (5.1) | `/manage/passcode/change/` → `manage_passcode_change` | `accounts/manage_change_passcode.html` |

### ⚙️ Khu quản lý (navbar xám, `base_manage.html`, `@manage_required`)
| Wireframe | Chức năng (mục) | URL → View | Template thật |
|---|---|---|---|
| [dashboard.html](../wireframe/dashboard.html) | Bảng điều khiển: số liệu + hồ sơ bé (5.1) | `/manage/` → `dashboard` | `accounts/dashboard.html` |
| [child-form.html](../wireframe/child-form.html) | Thêm/sửa/**xoá** hồ sơ bé (5.1) | `/manage/children/add|<pk>/edit/` → `child_add`/`child_edit`; nút Xoá → `.../delete/` → `child_delete` (modal xác nhận tên) | `accounts/child_form.html` |
| [topics.html](../wireframe/topics.html) | Quản lý chủ đề (5.2) | `/manage/topics/` → `topic_manage` | `catalog/manage/topic_list.html` |
| *(dùng chung form)* | Thêm/sửa chủ đề (5.2) | `/manage/topics/add|<pk>/edit/` → `topic_form` | `catalog/manage/topic_form.html` |
| [words.html](../wireframe/words.html) | Quản lý từ vựng: lọc + tìm + phân trang (5.2) | `/manage/words/` → `word_manage` | `catalog/manage/word_list.html` |
| [wordform.html](../wireframe/wordform.html) | Form thêm/sửa từ (5.2) | `/manage/words/add|<pk>/edit/` → `word_form` | `catalog/manage/word_form.html` |
| [import.html](../wireframe/import.html) | Nhập CSV + **Xuất CSV** (backup) (5.2) | `/manage/import/` → `word_import`; nút Xuất → `/manage/export/` → `word_export` | `catalog/manage/word_import.html` |
| [progress.html](../wireframe/progress.html) | Tiến độ của bé (5.1) | `/manage/progress/` → `progress` | `accounts/progress.html` |

### Ghi chú map
- **22 file wireframe** phủ toàn bộ chức năng đã làm (GĐ 0/1/2/4). Chưa có wireframe cho **GĐ 3** (chấm điểm phát âm) và **GĐ 5** (ngữ pháp/huy hiệu) vì chưa làm.
- **Trang chủ khu bé** (`kid_home.html`) không có thẻ riêng ở mục lục wireframe — điều hướng vào từ chính các thẻ khu của bé.
- **Màn "đặt" và "nhập" passcode** dùng **chung 1 URL** (`/manage/unlock/`): view tự chọn form theo `ManagePasscode.is_set`. Wireframe tách 2 file để xem cả 2 trạng thái.
- **Form chủ đề** không có thẻ mục lục riêng (gộp ý trong màn Quản lý chủ đề) nhưng template thật `topic_form.html` vẫn tồn tại — nếu cần wireframe riêng, thêm `topicform.html` cho đối xứng với `wordform.html`.
- **`game-match.html`** kiêm luôn minh hoạ **màn kết quả ⭐** (cùng game lật thẻ) — logic sao thật do `stars_from_ratio` (mục 5.4) quyết định khi `submit`.
- **Khung wireframe** (navbar mẫu, thanh điều hướng trước/sau) nằm chung trong `assets/wf-frame.*`, không phải template thật; khi map giao diện chỉ đối chiếu **phần thân màn**.
