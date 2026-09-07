# EngForMyChild — hướng dẫn nhanh cho Claude

Web học tiếng Anh **chạy local** cho bé 6–7 tuổi (phát âm / từ vựng / ngữ pháp qua trò chơi).
Django server-rendered + Alpine.js, SQLite, TTS `edge-tts`, ASR `faster-whisper` (service riêng).

> Quy ước coding đầy đủ nằm ở skill **`eng-coding`** (`.claude/skills/eng-coding/SKILL.md`) —
> đọc skill đó trước khi viết/sửa code. File này chỉ là bản đồ + các bẫy hay gặp.

## Bản đồ mã nguồn

| Thư mục | Nội dung |
|---|---|
| `web/core/` | `AuditedModel`, `YesNo`, `CurrentUserMiddleware`, `manage_required`, templatetags dùng chung |
| `web/accounts/` | Auth phụ huynh, `ChildProfile`, passcode khu quản lý, trang chủ bé, dashboard |
| `web/catalog/` | `Topic`/`Word`/`AudioClip`, TTS + IPA, import/export CSV, quản lý nội dung |
| `web/games/` | `GameType`, `engine/` (mỗi game 1 module), view chơi chung, `GameResult` |
| `web/pronunciation/` | Luyện đọc, ghi âm, gọi ASR, `Attempt` |
| `web/progress/` | Sao, huy hiệu, linh vật, màn tiến độ |
| `asr/` | Service FastAPI + faster-whisper (Docker), gọi qua `ASR_URL` |
| `wireframe/` | 25 màn HTML tĩnh xem trước — **phải đồng bộ tay** khi đổi UI |

## Lệnh hay dùng

```powershell
.\.venv\Scripts\python.exe web\manage.py <lệnh>     # LUÔN chạy qua đường dẫn web\manage.py
.\.venv\Scripts\python.exe web\manage.py test core accounts catalog games pronunciation progress
docker compose up                                    # khi cần kèm service ASR
```

## Bẫy đã từng gây bug — đọc kỹ

1. **Đường dẫn SQLite** — `settings.py` neo file DB tuyệt đối vào `BASE_DIR`. **KHÔNG gỡ đoạn neo.**
   Nếu "đăng nhập đúng mà báo sai": in `settings.DATABASES['default']['NAME']` xem có đọc nhầm file DB không.
2. **Cờ Y/N không phải Boolean** — dùng `CharField(max_length=1)` `'Y'`/`'N'`.
   Viết `if obj.active_flag:` là **sai** (chuỗi `'N'` vẫn truthy) → so sánh `== 'Y'` hoặc dùng `@property`.
3. **`json_script` không kèm `json.dumps`** — view truyền dict/list thuần; mã hoá 2 lần khiến client
   nhận chuỗi thay vì object, màn hỏng **mà không báo lỗi**.
4. **Script phụ thuộc Bootstrap** phải nằm trong `{% block extra_js %}`, không để trong `content`.
5. **Phân trang** — chỉ gọi `previous_page_number`/`next_page_number` bên trong `{% if has_previous %}`/`has_next`.
6. **CSS dùng `px`**, không `rem`/`em`.

## Thêm game mới

Tạo 1 module trong `web/games/engine/` (expose `build_round(words, count)` + `score_round(payload)`)
và 1 bản ghi `GameType` trong DB. **Không sửa** màn chọn game hay engine tính sao.
Logic chấm câu hỏi trắc nghiệm đã có sẵn: `engine/base.py` → `score_choice_round()`, `stars_from_ratio()`.

JS dùng chung cho mọi màn game ở `web/static/js/game-common.js` (`gameCommon.postJson`,
`playHintOnLoad`, `starText`) và hiệu ứng ở `kidfx.js` — **không copy lại `getCookie`/submit** vào template.
Header + màn kết thúc dùng include `templates/games/_play_header.html`, `_play_finished.html`.

## Khi sửa xong nhớ

- Đổi model → `makemigrations` + `migrate`, và cập nhật **ERD Mermaid** trong `docs/ThietKeDuLieu.md`.
- Đổi giao diện → đồng bộ `wireframe/` (xem `wireframe/README.md`).
- Chạy test xanh trước khi báo xong. TTS/ASR luôn **mock** trong test.
