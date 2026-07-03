---
name: eng-coding
description: Tiêu chuẩn & quy ước coding cho dự án EngForMyChild (website học tiếng Anh chạy local cho bé 6–7 tuổi — phát âm/từ vựng/ngữ pháp qua trò chơi; Django + Bootstrap + HTMX + Alpine.js, ASR faster-whisper, TTS edge-tts, Docker, SQLite). Dùng MỖI KHI viết hoặc sửa code trong dự án này — models, views, forms, templates, urls, migrations, game module, service TTS/ASR. Đọc skill này trước khi tạo file/màn hình mới.
---

# Tiêu chuẩn coding — Dự án EngForMyChild

Mục tiêu: mọi lần code đều theo cùng một khuôn để dễ đọc, dễ bảo trì. Đối tượng người dùng cuối là **bé 6–7 tuổi** → giao diện ưu tiên ít chữ, nhiều hình & âm thanh, nút to.

## 1. Ngữ cảnh dự án
- **Mục đích:** web học tiếng Anh chạy local cho bé. Ưu tiên **Phát âm → Từ vựng → Ngữ pháp**, bọc trong **trò chơi**. Dữ liệu (từ vựng, bản ghi của bé) **thu thập dần vào local**.
- **Stack:** Python 3.11 · Django 5.x (hoặc 4.2 LTS) · Django Templates + Bootstrap 5 + **HTMX** + **Alpine.js** (server-rendered, KHÔNG SPA).
- **CSDL:** SQLite (cả dev lẫn chạy local). Không dùng MySQL/Postgres.
- **Audio/ASR:** TTS sinh bằng `edge-tts` (cache mp3 vào `media/`), IPA bằng `eng-to-ipa`; chấm phát âm bằng `faster-whisper` chạy ở **service `asr` riêng** (FastAPI), gọi qua HTTP nội bộ.
- **Đóng gói:** Docker Compose — `web` (Django) + `asr` (faster-whisper). DB + `media/` gắn volume để giữ dữ liệu.
- **Ngôn ngữ giao diện:** **tiếng Việt + Anh song song** — hướng dẫn/nhãn tiếng Việt, nội dung học tiếng Anh.
- **Miễn phí & mã nguồn mở** toàn bộ; **khi học không cần internet** (audio đã cache, ASR local).
- **Tài liệu nguồn (đọc khi cần):** `docs/YeuCau.md`, `docs/ThietKeDuLieu.md`, `docs/CongNghe.md`.

## 2. Bố cục & cách chạy
- Source Django trong `web/`; service ASR trong `asr/`; tài liệu trong `docs/`; venv ở `.venv` (gốc).
- Apps: `core` (base model + mixin + templatetags), `accounts` (auth phụ huynh + `ChildProfile` + trang chủ), `catalog` (Topic/Word/AudioClip/Sentence + import + TTS/IPA), `games` (GameType + khuôn game + chơi chung), `pronunciation` (luyện phát âm + ghi âm + ASR + Attempt), `progress` (GameResult + huy hiệu + tiến độ).
- **Chạy lệnh Django qua venv:**
  ```powershell
  .\.venv\Scripts\python.exe web\manage.py <lệnh>
  ```
- Chạy bằng Docker khi cần kèm ASR: `docker compose up`.
- Sau khi đổi model: `makemigrations` → `migrate` → `check`. Không sửa migration đã áp dụng bằng tay.
- **File DB SQLite phải neo tuyệt đối vào `BASE_DIR` (QUAN TRỌNG — đã từng gây bug):** `DATABASE_URL=sqlite:///db.sqlite3` là đường dẫn **tương đối**, nên file DB thực dùng phụ thuộc thư mục đang đứng khi gõ lệnh → dễ tạo `createsuperuser`/`migrate` vào file này nhưng `runserver` đọc file khác (admin "đúng mật khẩu vẫn báo sai", có 2 file `db.sqlite3`). `settings.py` đã neo: nếu engine là sqlite và `NAME` không tuyệt đối thì ép `BASE_DIR / basename(NAME)`. **KHÔNG gỡ đoạn neo này**; luôn chạy lệnh `manage.py` qua đường dẫn `web\manage.py` (mục trên) để nhất quán. Nếu nghi "đăng nhập sai vô lý", việc ĐẦU TIÊN: in `settings.DATABASES['default']['NAME']` xem server đọc đúng file DB chưa, và `find . -name db.sqlite3` xem có file thừa không.
- **Chẩn đoán đăng nhập thất bại:** dùng `ParentLoginView` (ghi log `eng.auth` lý do form lỗi). Khi sự cố: xem `web/logs/app-*.log` dòng `eng.auth` — `invalid_login` = sai credential/đọc nhầm DB (xem trên); lỗi CSRF/required = vấn đề token/cookie, không phải mật khẩu. KHÔNG đoán mò mật khẩu — kiểm `authenticate()`/`check_password()` trực tiếp trên đúng DB trước.

## 3. Quy ước Models
- Tên field & code bằng tiếng Anh; `verbose_name` (label) bằng **tiếng Việt**.
- Enum dùng `models.TextChoices` (lồng trong model). Field loại/trạng thái → CharField + `choices`.
- **Cờ Y/N (QUAN TRỌNG):** KHÔNG dùng `BooleanField`. Dùng `CharField(max_length=1)` lưu `'Y'/'N'`, default rõ ràng. Thêm `@property` trả bool (vd `.active`).
  - So sánh bằng `== 'Y'` hoặc dùng property. **TUYỆT ĐỐI KHÔNG** viết `if obj.active_flag:` khi field là chuỗi (chuỗi `'N'` vẫn truthy).
- **Sở hữu dữ liệu:** model thuộc phụ huynh có FK `owner` → `settings.AUTH_USER_MODEL`, `on_delete=PROTECT` (vd `ChildProfile`). Dữ liệu của bé (`Attempt`, `GameResult`) gắn qua `ChildProfile`.
- **Nội dung học dùng chung** (`Topic`, `Word`, `AudioClip`, `Sentence`, `GameType`, `Badge`) KHÔNG thuộc owner — là kho chung cho mọi bé.
- Đặt `related_name` rõ ràng, tránh trùng tên có sẵn của Django.
- Mỗi model có: `class Meta` (`verbose_name`, `verbose_name_plural` tiếng Việt, `ordering`), `UniqueConstraint`/`Index` khi cần, và `__str__`.
- **Audit:** bảng nghiệp vụ KẾ THỪA `core.models.AuditedModel` (`created_at`, `updated_at`, `created_by`, `updated_by`). KHÔNG khai báo lại. `created_by`/`updated_by` tự điền từ user đăng nhập qua `CurrentUserMiddleware` — không gán tay trong view. (Bản ghi do bé tạo lúc chơi có thể không có user → cho phép null.)
- Xoá mềm: dùng cờ `active='N'` / trạng thái, KHÔNG xoá cứng dữ liệu có lịch sử (đặc biệt `Attempt`/`GameResult`).
- **File media:** audio TTS lưu `media/audio/`, hình từ vựng `media/images/`, ghi âm bé `media/recordings/`. Đặt `upload_to` tương ứng. Lưu **đường dẫn** (FileField/ImageField), KHÔNG lưu blob nhị phân vào DB.
- **Tương thích SQLite ↔ MySQL (BẮT BUỘC — xem `docs/ThietKeDuLieu.md` mục 0.1):** đổi DB chỉ bằng `DATABASE_URL`, không sửa model. Quy tắc khi viết model: luôn khai báo `max_length`; cột `unique`/`db_index`/trong `UniqueConstraint` giữ `max_length ≤ 191` (utf8mb4); KHÔNG đặt `unique`/`db_index` trên `TextField`; dùng `JSONField` (không nhét JSON vào TextField); chỉ dùng Django migrations (không SQL DDL tay) và ORM (không `.extra()`/raw SQL đặc thù DB); `USE_TZ=True`, `DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'`. Logic phụ thuộc hoa-thường phải dùng `__iexact` rõ ràng (SQLite phân biệt, MySQL ci thì không).

## 4. Views & quyền
- View khu **phụ huynh** (quản trị nội dung, hồ sơ bé, tiến độ) bọc `@login_required`.
- **Lọc theo chủ sở hữu** với dữ liệu riêng của phụ huynh: `ChildProfile.objects.filter(owner=request.user, ...)`. Không để phụ huynh thấy hồ sơ bé của người khác. Dùng `get_object_or_404` + kiểm tra `owner`.
- View khu **bé chơi/học** (chọn chủ đề, chơi game, luyện phát âm) gắn theo `ChildProfile` đang chọn; giữ đơn giản, không bắt đăng nhập phức tạp.
- Ưu tiên class-based views hoặc function views gọn.
- Tương tác động (cập nhật mảnh trang, nộp kết quả game) ưu tiên **HTMX**; trạng thái client nhỏ (lật thẻ, đếm giờ, kéo–thả) dùng **Alpine.js** — tránh viết JS rời rạc.

## 5. Game — kiến trúc "Khuôn chơi + Dữ liệu" (BẮT BUỘC khi thêm game)
- Tách **luật chơi** (code) khỏi **nội dung** (kho `Word`/`Sentence`). Game lấy từ ngẫu nhiên theo `topic`/`level`, KHÔNG tạo dữ liệu riêng cho từng game.
- Mỗi khuôn game là **một module trong `games/`** (vd `games/listen_pick.py`) expose interface chuẩn:
  ```python
  def build_round(topic, level, count): ...   # -> dict dữ liệu một vòng chơi
  def score_round(payload): ...               # -> {'stars': int, 'score': int}
  ```
- Mỗi game có một bản ghi `GameType` (DB): `code`, `name_vi`, `icon`, `module`, `min_words`, `needs_image`, `needs_asr`, `order`, `active`.
- **Thêm game mới = thêm 1 module + 1 bản ghi `GameType`** → tự hiện trên màn chọn game. KHÔNG sửa màn chọn game, KHÔNG viết lại phần điểm/sao (dùng chung trong `games`).
- View chơi chung đọc `GameType` → gọi `build_round`/`score_round` của module → lưu `GameResult` → cộng sao.

## 6. Audio / TTS / ASR
- **Phát audio:** luôn lấy qua hàm tiện ích chung (vd `catalog.audio.get_clip(word)`): ưu tiên `AudioClip` có (recorded/is_default); nếu chưa có thì sinh TTS, **lưu lại** rồi trả về (cache — không gọi TTS lại lần sau). KHÔNG gọi `edge-tts` trực tiếp rải rác trong view.
- **IPA:** sinh tự động bằng `eng-to-ipa` khi `phonetic` trống; không nhập tay nếu không cần.
- **ASR:** chỉ gọi service `asr` qua `ASR_URL` (từ `.env`), gói trong một service/hàm riêng (vd `pronunciation.asr.score(audio, target)`); xử lý lỗi mạng/timeout gọn, không để 500 khi ASR tắt — báo "thử lại" thân thiện. Giọng bé **không gửi ra ngoài**, chỉ tới service local.
- **Chấm điểm = sao, KHÔNG điểm gây áp lực:** quy score → 0–3 sao; sai thì khuyến khích nghe lại, không trừ.

## 7. Forms
- Dùng `ModelForm`. Gắn class Bootstrap (`form-control`, `form-select`) qua widget hoặc helper.
- Nhãn/thông báo lỗi tiếng Việt.

## 8. Templates
- Đều `{% extends 'base.html' %}`; đặt trong `web/templates/` hoặc `templates/` của app.
- **Thân thiện trẻ em:** nút to, icon (Bootstrap Icons) + emoji, ít chữ; thao tác chính có nút 🔊 nghe hướng dẫn. Màu tươi qua biến CSS (`--brand`...).
- Form POST luôn có `{% csrf_token %}`.
- Link bằng `{% url 'app:name' %}`, KHÔNG hardcode đường dẫn.
- Hiển thị cờ Y/N qua `get_<field>_display` hoặc property, không in thẳng `'Y'/'N'`.
- **Phân trang:** chỉ render `page_obj.previous_page_number`/`next_page_number` BÊN TRONG `{% if page_obj.has_previous %}`/`has_next` (gọi ở trang đầu/cuối raise `EmptyPage` → 500).
- **Nạp JS:** Bootstrap bundle + Alpine.js + `app.js` nạp ở CUỐI `base.html`. Alpine nạp với `defer` (Alpine khởi tạo sau khi DOM có `x-data`). Script trang phụ thuộc `bootstrap` (vd `new bootstrap.Modal`) PHẢI đặt trong `{% block extra_js %}` (render sau bundle) — KHÔNG để trong `{% block content %}` (chạy trước → `bootstrap is not defined`).
- **Alpine.js:** dùng cho trạng thái client cục bộ của game (lật thẻ, chọn đáp án, đếm giờ). Giữ logic trong `x-data` gọn; logic nặng/đụng server đẩy sang HTMX hoặc view.
- **Truyền dữ liệu sang JS dùng `{{ data|json_script:"id" }}` (QUAN TRỌNG — đã từng gây bug):** view truyền **đối tượng Python thuần (dict/list)**, template dùng `json_script`; KHÔNG `json.dumps()` ở view rồi lại `json_script` (mã hoá 2 lần → client `JSON.parse` ra **chuỗi**, không phải object, game/màn không chạy mà KHÔNG báo lỗi). Client đọc: `JSON.parse(document.getElementById("id").textContent)`. Mỗi màn truyền JSON kiểu này PHẢI có test parse lại khẳng định ra dict/list (xem `games`/`pronunciation` tests).

## 9. URLs
- Mỗi app có `urls.py` riêng với `app_name` (namespace); include vào `config/urls.py`.
- **Đường dẫn (path) bằng tiếng Anh**, chữ thường, nối bằng `-`. Tên url (`name=`) cũng tiếng Anh.
- Quy ước CRUD: list `''` · create `'add/'` · detail `'<int:pk>/'` · update `'<int:pk>/edit/'` · action khác `'<int:pk>/<action>/'`.
- Prefix include theo tên app: `catalog/`, `games/`, `pronunciation/`, `progress/`...
- Trong code/template luôn dùng `{% url 'app:name' %}` / `reverse('app:name')`, KHÔNG hardcode path.

## 10. Style
- Tuân thủ PEP 8: thụt 4 space, import gom nhóm (chuẩn → bên thứ ba → nội bộ).
- Tên biến/hàm rõ nghĩa; không lặp code — tách hàm/property/mixin dùng chung (đặt ở `core`).

### 10.1. Comment tiếng Việt (BẮT BUỘC)
- **Luôn thêm comment tiếng Việt:** docstring cho mỗi module/class/hàm; comment giải thích **"vì sao"** cho logic không hiển nhiên (vd luật chấm sao, cache TTS).
- Ngắn gọn, đúng mật độ code xung quanh; không comment lại điều đã rõ từ tên.

### 10.2. Dễ mở rộng & dễ bảo trì
- Ưu tiên tái sử dụng: gom logic chung vào base model / mixin / hàm tiện ích (`core`, `games` engine, `catalog.audio`), KHÔNG copy-paste.
- Tách trách nhiệm: model giữ dữ liệu + nghiệp vụ cơ bản; view mỏng; logic phức tạp (TTS, ASR, build/score game) đưa vào service/module riêng dễ test.
- **Dữ liệu tách rời code:** thêm từ vựng/game/huy hiệu qua dữ liệu + cấu hình (`GameType`, CSV import), hạn chế sửa code. Tránh chuỗi/số cứng rải rác — dùng `TextChoices`, hằng số, `.env`.
- Giữ nhất quán với code & quy ước hiện có để người sau dễ đọc.

## 11. Logging
- Cấu hình `LOGGING` trong `config/settings.py`. Trong code dùng `logger = logging.getLogger('eng')` (hoặc `'eng.<chức năng>'`, vd `'eng.tts'`, `'eng.asr'`). **KHÔNG dùng `print()`** cho thông tin vận hành.
- Lỗi: `logger.exception(...)` trong khối `except` để có traceback (đặc biệt khi gọi ASR/TTS).
- Mức log chỉnh qua `.env`: `LOG_LEVEL`.

## 12. Test (BẮT BUỘC)
- **Mỗi view/controller phải có test** trong `tests.py` (hoặc package `tests/`) của app. Dùng `django.test.TestCase` + `self.client` + `reverse('app:name')` (KHÔNG hardcode URL).
- Tối thiểu kiểm:
  1. **Yêu cầu đăng nhập** (view phụ huynh): chưa đăng nhập → redirect `/login/`.
  2. **Lọc theo owner:** không thấy/sửa được hồ sơ bé của phụ huynh khác (404).
  3. **Happy path:** GET 200; POST tạo/sửa thành công, lưu đúng (kể cả `owner`).
  4. **Nghiệp vụ riêng:** import CSV tạo đúng Word/Topic + idempotent; `build_round`/`score_round` của game (test thuần, không cần HTTP); chấm sao đúng ngưỡng.
- **TTS/ASR trong test:** **mock** (không gọi mạng/model thật) — test logic cache/chấm, không test chất lượng audio.
- Chạy test (liệt kê app vì source trong `web/`):
  `.\.venv\Scripts\python.exe web\manage.py test core accounts catalog games pronunciation progress`
  (thêm app mới vào danh sách khi tạo). Phải xanh trước khi báo xong.

## 13. Đồng bộ tài liệu (BẮT BUỘC)
- **Khi đổi nghiệp vụ / mô hình dữ liệu / yêu cầu / stack:** cập nhật tài liệu liên quan — `docs/YeuCau.md`, `docs/ThietKeDuLieu.md`, `docs/CongNghe.md`. Tài liệu và code KHÔNG được mâu thuẫn.
- **Khi đổi model (thêm/bớt bảng, field, quan hệ):** cập nhật **sơ đồ ERD Mermaid** trong `docs/ThietKeDuLieu.md` (mục 1) cho khớp — bảng/field/quan hệ trong ERD phải đúng với model thực tế. ERD lược bỏ cột audit cho gọn (mọi bảng nghiệp vụ đều có do `AuditedModel`).
- Thêm game/khuôn chơi mới → cập nhật bảng game trong `docs/ThietKeDuLieu.md`.
- **Khi sửa GIAO DIỆN (template khu bé/quản lý, `style.css`, thêm màn/game mới) → ĐỒNG BỘ WIREFRAME** (`wireframe/`, xem `wireframe/README.md` mục "Đồng bộ giao diện"):
  1. Đổi `web/static/css/style.css` hoặc `web/static/vendor/*` → copy sang `wireframe/assets/` (2 lệnh `Copy-Item` trong README).
  2. Sửa bố cục màn có sẵn → cập nhật file wireframe tương ứng (tra bảng map ở `docs/ThietKeCoBan.md` mục 10).
  3. Thêm màn/game mới → thêm file `wireframe/<tên>.html` + đăng ký vào `wireframe/assets/wf-frame.js` (mảng `WF_SCREENS`) + thẻ trong `wireframe/index.html` + dòng vào bảng map `docs/ThietKeCoBan.md` mục 10.
  Wireframe là bản tĩnh: hình của từ minh hoạ bằng emoji (thay `w.image` thật); màn động chỉ vẽ một trạng thái đại diện.

## 14. Checklist trước khi báo "xong"
1. `web\manage.py check` không lỗi.
2. Đã `makemigrations` + `migrate` nếu đổi model.
3. View phụ huynh đã lọc `owner=request.user`.
4. Không dùng `BooleanField`; cờ là `'Y'/'N'` và so sánh đúng cách.
5. Game mới theo kiến trúc khuôn+dữ liệu (module + `GameType`), không sửa màn chọn game/engine sao.
6. Audio lấy qua hàm chung có cache; ASR gọi qua service, xử lý lỗi thân thiện.
7. Template kế thừa `base.html`, có CSRF, dùng `{% url %}`, tiếng Việt, thân thiện trẻ em.
8. Đã viết test cho phần mới và `manage.py test` chạy xanh (TTS/ASR mock).
9. Tài liệu `docs/*.md` khớp với thay đổi (mục 13); nếu đổi model → **đã cập nhật sơ đồ ERD Mermaid** trong `docs/ThietKeDuLieu.md`.
10. Nếu sửa giao diện (template/`style.css`/thêm màn) → **đã đồng bộ wireframe** (mục 13: copy `style.css`, cập nhật/thêm file wireframe, `wf-frame.js`, `index.html`, bảng map mục 10).
