# Thiết kế dữ liệu — EngForMyChild

> Tài liệu mô hình dữ liệu + kiến trúc trò chơi. Mục tiêu cốt lõi: **dữ liệu tách rời code** → thêm từ vựng và trò chơi dễ dàng, ít sửa code.

## 0. Quy ước chung (theo skill `eng-coding`)
- Tên field/code **tiếng Anh**; `verbose_name` (label) **tiếng Việt**.
- Cờ Y/N: `CharField(max_length=1)` lưu `'Y'/'N'` + `@property` trả bool. **KHÔNG** `BooleanField`.
- Bảng nghiệp vụ kế thừa `core.models.AuditedModel` (`created_at`, `updated_at`, `created_by`, `updated_by`).
- Dữ liệu thuộc phụ huynh có FK `owner` → `AUTH_USER_MODEL`, `on_delete=PROTECT`.
- Enum dùng `models.TextChoices`. Xoá mềm bằng cờ/trạng thái.

---

## 0.1. Tương thích đa CSDL (SQLite hôm nay → MySQL về sau) — BẮT BUỘC

> Thiết kế để **đổi từ SQLite sang MySQL chỉ bằng đổi cấu hình kết nối**, KHÔNG sửa model/migration. Django ORM lo phần lớn; phần còn lại là vài quy tắc dưới đây phải tuân từ đầu (sửa sau rất tốn công vì phải đổi migration đã chạy).

**Kết nối tách khỏi code:**
- Cấu hình DB qua biến môi trường `DATABASE_URL` trong `.env` (dùng `dj-database-url` hoặc tự parse). SQLite: `sqlite:///db.sqlite3`; MySQL: `mysql://user:pass@host:3306/eng?charset=utf8mb4`.
- `settings.py` đọc `DATABASE_URL`, KHÔNG hardcode engine. Đổi DB = đổi 1 dòng `.env` + cài driver `mysqlclient`.

**Charset (QUAN TRỌNG — emoji & IPA):**
- MySQL phải dùng **`utf8mb4`** (lưu được emoji 🐾🦜 trong `icon`, ký tự IPA trong `phonetic`). Đặt khi tạo DB: `CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`, và `OPTIONS={'charset': 'utf8mb4'}` trong settings cho MySQL. SQLite luôn UTF-8 nên dev không lộ lỗi — dễ quên cho tới khi chạy MySQL; vì vậy chốt ngay.

**Độ dài cột & index (giới hạn MySQL):**
- MySQL **bắt buộc `max_length`** cho mọi `CharField` — luôn khai báo, đừng để mặc định quá lớn.
- Cột có **`db_index`/`unique`/nằm trong `UniqueConstraint`** phải đủ ngắn: với utf8mb4, mỗi ký tự tối đa 4 byte, giới hạn index ~3072 byte → **giữ `max_length` của cột index ≤ 191** cho an toàn tuyệt đối (quy tắc 191 quen thuộc của MySQL+utf8mb4). Áp dụng cho `slug`, `code`, `text_en`... khi chúng nằm trong unique/index.
- **KHÔNG đặt `unique`/`db_index` trên `TextField`** (MySQL cần prefix length, Django không tự thêm → migrate lỗi). Nội dung dài (vd mô tả) để TextField **không** index; thứ cần tra cứu/unique thì để CharField ngắn.

**Kiểu dữ liệu an toàn cho cả hai:**
- **Cờ Y/N** = `CharField(max_length=1)` (đã quy ước) — bằng nhau trên mọi DB, không dùng `BooleanField` (tránh khác biệt 0/1 vs true/false giữa backend).
- **Số:** dùng `IntegerField`/`PositiveSmallIntegerField`/`DecimalField` — tránh kiểu phụ thuộc DB. `AutoField`/`BigAutoField` để Django lo khoá chính (đặt `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`).
- **Thời gian:** `DateTimeField` (Django chuẩn hoá UTC) — nhất quán hai DB. Bật `USE_TZ = True`.
- **JSON:** `models.JSONField` (vd `Badge.condition`) — Django hỗ trợ trên cả SQLite (3.38+) và MySQL (5.7+). KHÔNG tự nhét JSON vào TextField rồi parse tay.
- **File/ảnh/audio:** lưu **đường dẫn** qua `FileField`/`ImageField` (file nằm trong `media/`), KHÔNG lưu blob nhị phân vào DB → không phụ thuộc kiểu BLOB của DB, và nhẹ.

**Migration & truy vấn:**
- Dùng **Django migrations** cho mọi thay đổi schema; KHÔNG viết SQL DDL tay. Migration sinh ra trung tính, chạy được trên cả hai engine.
- **KHÔNG dùng `.extra()` / raw SQL** đặc thù một DB. Nếu cần biểu thức, dùng ORM (`F`, `Q`, `annotate`, functions trong `django.db.models.functions`).
- **So sánh chuỗi/sắp xếp:** SQLite mặc định **phân biệt hoa-thường** với so khớp Unicode, MySQL (`utf8mb4_unicode_ci`) **không** phân biệt — nếu logic phụ thuộc, dùng `__iexact`/`lower=...` rõ ràng thay vì dựa hành vi mặc định.
- **Test trên cả hai trước khi tin là tương thích:** chạy test suite với SQLite (mặc định) và một lần với MySQL (qua Docker) khi chuẩn bị chuyển — đó là cách chắc chắn duy nhất.

**Triển khai MySQL khi cần (không đổi code):**
1. Thêm service `db` (MySQL 8, `utf8mb4`) vào `docker-compose.yml`, volume riêng.
2. Cài `mysqlclient` vào `web` (cần lib hệ thống — thêm trong Dockerfile của `web`).
3. Đổi `DATABASE_URL` trong `.env` sang `mysql://...`.
4. `migrate` (schema tạo lại trên MySQL) → nạp lại dữ liệu (`dumpdata`/`loaddata` hoặc import CSV).

---

## 1. Sơ đồ tổng quan

```
User (phụ huynh)
 └─< ChildProfile (hồ sơ bé)
        ├─< Attempt        (mỗi lần luyện phát âm)
        └─< GameResult     (mỗi ván chơi)

Topic (chủ đề)
 ├─< Word (từ vựng)
 │     ├─< AudioClip   (1..n audio/từ: tts hoặc thu sẵn)
 │     └─< Attempt     (bé đã luyện từ này)
 └─< Sentence (câu mẫu — ngữ pháp, GĐ sau)

GameType (loại game — cấu hình)  ──< GameResult
Reward / Badge (huy hiệu)        ──< ChildProfile (mở khoá dần)
```

### Sơ đồ ERD (Mermaid)

> Render được trên GitHub và VSCode (preview Markdown / Mermaid). **Cập nhật sơ đồ này mỗi khi đổi model** (thêm/bớt bảng, field, quan hệ) — xem skill `eng-coding` mục 13.

```mermaid
erDiagram
    User ||--o{ ChildProfile : "owner (PROTECT)"
    ChildProfile ||--o{ Attempt : "luyện phát âm"
    ChildProfile ||--o{ GameResult : "ván chơi"
    ChildProfile ||--o{ ChildBadge : "đạt huy hiệu"

    Topic ||--o{ Word : "words"
    Topic ||--o{ Sentence : "sentences"
    Word ||--o{ AudioClip : "clips"
    Word ||--o{ Attempt : "từ luyện"

    GameType ||--o{ GameResult : "loại game"
    Topic ||--o{ GameResult : "chủ đề chơi"
    Badge ||--o{ ChildBadge : "huy hiệu"

    User {
        int id PK
        string username
    }
    ChildProfile {
        int id PK
        int owner_id FK "User, PROTECT"
        string name
        int birth_year
        string avatar
        string active "Y/N"
    }
    ManagePasscode {
        int id PK "singleton pk=1"
        string passcode_hash "băm, không lưu thô"
    }
    Topic {
        int id PK
        string name_en
        string name_vi
        string slug UK "max 100"
        string icon "emoji, utf8mb4"
        int order
        string active "Y/N"
    }
    Word {
        int id PK
        int topic_id FK
        string text_en "max 100, unique theo topic"
        string text_vi
        string phonetic "IPA, blank"
        string image "đường dẫn, blank"
        int level
        string active "Y/N"
    }
    AudioClip {
        int id PK
        int word_id FK
        string source "tts/recorded"
        string voice "blank"
        string file "mp3 trong media/"
        string is_default "Y/N"
    }
    Sentence {
        int id PK
        int topic_id FK
        string text_en
        string text_vi
        string pattern
        string active "Y/N"
    }
    Attempt {
        int id PK
        int child_id FK
        int word_id FK
        string recording "audio bé"
        string asr_text "blank"
        int score "0-100"
        int stars "0-3"
    }
    GameType {
        int id PK
        string code UK "max 50"
        string name_vi
        string icon
        string module "vd games.listen_pick"
        int min_words
        string needs_image "Y/N"
        string needs_asr "Y/N"
        int order
        string active "Y/N"
    }
    GameResult {
        int id PK
        int child_id FK
        int game_type_id FK
        int topic_id FK "null"
        int stars
        int duration_sec
    }
    Badge {
        int id PK
        string code UK
        string name_vi
        string icon
        json condition "điều kiện mở"
    }
    ChildBadge {
        int id PK
        int child_id FK
        int badge_id FK
        datetime earned_at
    }
```

> Lược bỏ các cột audit (`created_at`, `updated_at`, `created_by`, `updated_by`) khỏi sơ đồ cho gọn — mọi bảng nghiệp vụ đều có (kế thừa `AuditedModel`). `||--o{` = một–nhiều; `UK` = unique; `FK`/`PK` = khoá ngoài/khoá chính.

---

## 2. Nhóm CATALOG — nội dung học (thêm dần)

### Topic — chủ đề
| field | kiểu | ghi chú |
|---|---|---|
| `name_en` | CharField | vd "Animals" |
| `name_vi` | CharField | vd "Động vật" |
| `slug` | SlugField(max_length=100, unique) | định danh URL — cột unique nên ≤191 (utf8mb4) |
| `icon` | CharField(max_length=50) | tên icon / emoji 🐾 (cần utf8mb4 trên MySQL) |
| `order` | IntegerField | thứ tự hiển thị |
| `active` | CharField('Y'/'N') | bật/tắt |

### Word — từ vựng (đơn vị học chính)
| field | kiểu | ghi chú |
|---|---|---|
| `topic` | FK Topic | `related_name='words'` |
| `text_en` | CharField(max_length=100) | từ tiếng Anh, vd "cat" — nằm trong UniqueConstraint nên ≤191 |
| `text_vi` | CharField(max_length=150) | nghĩa, vd "con mèo" |
| `phonetic` | CharField(max_length=150, blank) | IPA — **tự sinh** bằng `eng-to-ipa` nếu trống (cần utf8mb4) |
| `image` | ImageField, blank | hình minh hoạ; trống → dùng emoji/hình mặc định |
| `level` | IntegerField | độ khó (lọc theo trình độ bé) |
| `active` | CharField('Y'/'N') | |

`class Meta`: `ordering=['topic','text_en']`, `UniqueConstraint(topic, text_en)`. Kế thừa `AuditedModel`.

### AudioClip — audio phát âm (nhiều nguồn/từ)
| field | kiểu | ghi chú |
|---|---|---|
| `word` | FK Word | `related_name='clips'` |
| `source` | CharField choices | `tts` / `recorded` |
| `voice` | CharField, blank | giọng TTS (vd `en-US-AnaNeural`) |
| `file` | FileField | mp3 trong `media/audio/` |
| `is_default` | CharField('Y'/'N') | clip ưu tiên phát |

**Vì sao tách AudioClip khỏi Word:** một từ có thể có nhiều audio (TTS nhiều giọng + bản thu thật). Ưu tiên `recorded`/`is_default='Y'`; nếu chưa có thì sinh TTS và lưu lại (cache). Lần sau dùng file đã có → không gọi TTS lại.

### Sentence — câu mẫu (ngữ pháp, GĐ sau)
| field | kiểu | ghi chú |
|---|---|---|
| `topic` | FK Topic | |
| `text_en` | CharField | vd "I see a cat" |
| `text_vi` | CharField | |
| `pattern` | CharField | mẫu câu, vd "I see a/an ___" |
| `active` | CharField('Y'/'N') | |

---

## 3. Nhóm HỌC SINH & TIẾN ĐỘ — dữ liệu thu thập

### ChildProfile — hồ sơ bé
| field | kiểu | ghi chú |
|---|---|---|
| `owner` | FK User (PROTECT) | phụ huynh sở hữu |
| `name` | CharField | tên/biệt danh bé |
| `birth_year` | IntegerField | tính tuổi gợi ý `level` |
| `avatar` | CharField/ImageField | bé chọn avatar |
| `active` | CharField('Y'/'N') | |

> **Xoá hồ sơ bé (xoá cứng):** phụ huynh có thể xoá hẳn 1 bé ở màn sửa (phải xác nhận đúng tên). Vì `Attempt` và `GameResult` tham chiếu `ChildProfile` với `on_delete=CASCADE`, xoá bé sẽ **tự xoá theo** mọi lần luyện & ván chơi của bé. Riêng **file ghi âm** (`Attempt.recording` trong `media/recordings/`) do Django không tự xoá nên view `child_delete` **dọn tay** trước khi xoá bản ghi. Đây là ngoại lệ có chủ đích so với quy ước xoá mềm (app local, dữ liệu của chính gia đình).

### Attempt — mỗi lần luyện phát âm (dữ liệu tích luỹ)
| field | kiểu | ghi chú |
|---|---|---|
| `child` | FK ChildProfile | `related_name='attempts'` |
| `word` | FK Word | từ đang luyện |
| `recording` | FileField | bản ghi giọng bé (`media/recordings/`) |
| `asr_text` | CharField, blank | text faster-whisper nhận dạng |
| `score` | IntegerField | điểm khớp (0–100) → quy ra sao |
| `stars` | IntegerField | 0–3 sao |

### GameResult — mỗi ván chơi
| field | kiểu | ghi chú |
|---|---|---|
| `child` | FK ChildProfile | |
| `game_type` | FK GameType | |
| `topic` | FK Topic, null | chủ đề đã chơi |
| `stars` | IntegerField | sao đạt |
| `duration_sec` | IntegerField | thời lượng |
| `played_at` | (từ AuditedModel.created_at) | |

> `Attempt` + `GameResult` chính là phần **"thu thập dữ liệu dần vào local"**, dùng cho màn tiến độ của phụ huynh.

---

## 4. Nhóm GAME — kiến trúc "Khuôn chơi + Dữ liệu" (điểm mấu chốt)

**Triết lý:** tách **luật chơi** (code, ít, ổn định) khỏi **nội dung** (dữ liệu từ vựng, nhiều, thêm dần). Cùng một kho `Word` đổ vào **nhiều khuôn game** khác nhau → thêm từ thì mọi game **tự động** có nội dung mới, không sửa game.

### GameType — bảng cấu hình game (DB)
| field | kiểu | ghi chú |
|---|---|---|
| `code` | SlugField(max_length=50, unique) | định danh, vd `listen_pick`, `match_pairs`, `parrot` (unique → ≤191) |
| `name_vi` | CharField | tên hiển thị cho bé |
| `icon` | CharField | icon/emoji |
| `module` | CharField | đường dẫn module xử lý (vd `games.listen_pick`) |
| `min_words` | IntegerField | số từ tối thiểu để chơi được |
| `needs_image` | CharField('Y'/'N') | game có cần hình không |
| `needs_asr` | CharField('Y'/'N') | có cần service ASR không (game phát âm) |
| `order` | IntegerField | thứ tự trên màn chọn game |
| `active` | CharField('Y'/'N') | bật/tắt |

→ **Thêm game mới = thêm 1 module + 1 bản ghi `GameType`** → tự xuất hiện trên màn chọn game. Không sửa màn hình chọn game.

### Interface chung cho mọi khuôn game
Mỗi khuôn game là một **module trong `games/engine/`** (vd `games/engine/listen_pick.py`), expose hàm chuẩn:

```
build_round(words, count) -> dict          # tạo dữ liệu một vòng chơi từ danh sách Word
                                            # (chọn ngẫu nhiên từ + nhiễu)
score_round(payload) -> {score,total,stars} # chấm kết quả bé gửi lên
```

- View chung `games/<child_id>/<code>/<slug>/` đọc `GameType`, lọc Word của chủ đề, gọi `build_round()` của module (nạp qua `games/engine/registry.py`), render template `play_<module>.html`, nhận kết quả → `score_round()` → lưu `GameResult` → cộng sao. **Phần điểm/sao dùng chung** (`engine/base.py: stars_from_ratio`), không viết lại theo từng game.
- **Truyền round-data sang client:** view trả **dict thuần**, template dùng `{{ round_data|json_script:"round-data" }}` (KHÔNG `json.dumps` ở view — tránh mã hoá 2 lần). Xem skill `eng-coding` mục 8.

### Các khuôn game (cùng dùng kho Word)
| code (module) | tên | cách chơi | cần | trạng thái |
|---|---|---|---|---|
| `listen_pick` | Nghe & chọn | nghe audio → chọn đúng từ trong 4 | audio | **XONG (GĐ4)** |
| `match_pairs` | Lật thẻ tìm cặp | memory Anh↔Việt | — | **XONG (GĐ4)** |
| `match_word` | Nối hình ↔ từ | kéo từ về đúng hình | image | dự kiến |
| `parrot` | Nhại con vẹt 🦜 | nghe → lặp lại → ASR chấm | audio + ASR | GĐ3 (cần Docker) |
| `build_sentence` | Xếp câu (ngữ pháp) | kéo từ thành câu đúng | Sentence | GĐ5 |

> Thêm từ mới → mọi game tự có thêm nội dung, không đụng code. Thêm game mới = 1 module trong `games/engine/` + 1 bản ghi `GameType` (seed qua migration).

### Reward / Badge — huy hiệu (mở khoá dần)
| field | kiểu | ghi chú |
|---|---|---|
| `code` | SlugField | vd `zoo_animals` |
| `name_vi` | CharField | |
| `icon` | CharField | |
| `condition` | JSONField | điều kiện mở (vd `{"topic_done": "animals"}`) — JSONField chạy cả SQLite & MySQL |

Bảng nối `ChildBadge(child, badge, earned_at)` ghi huy hiệu bé đã đạt.

---

## 5. Nhập liệu — CSV import (thu thập đơn giản)

Lệnh `manage.py import_words <file.csv>`:
```csv
topic,text_en,text_vi,image_url
Animals,cat,con mèo,
Colors,red,màu đỏ,https://.../red.png
```
- Tự tạo `Topic` nếu chưa có (theo `name_en`).
- Tạo `Word`; nếu `phonetic` trống → sinh IPA (`eng-to-ipa`).
- Sinh **AudioClip TTS** (`edge-tts`) và cache vào `media/audio/`.
- `image_url` có → tải về `media/images/`; trống → để bé/phụ huynh bổ sung sau.
- Idempotent: chạy lại không tạo trùng (dựa `UniqueConstraint(topic, text_en)`).

> Quy trình thực tế: Google Sheet → export CSV → 1 lệnh import → có ngay từ + audio + IPA.

---

## 6. Apps Django (dự kiến)
- `core` — AuditedModel, mixin (vd `ListReturnMixin`), templatetags dùng chung, **decorator `manage_required`** (chặn khu quản lý: cần đăng nhập + passcode còn hạn).
- `accounts` — phụ huynh (auth) + `ChildProfile` + `ManagePasscode` (passcode khu quản lý, lưu hash) + **trang chủ khu của bé** + **bảng điều khiển khu quản lý** + màn **Tiến độ** + 3 màn passcode (nhập/đặt/đổi).
- `catalog` — `Topic`, `Word`, `AudioClip`, `Sentence` + **màn quản lý CRUD chủ đề/từ + nhập CSV qua web** (URL khu quản lý tách ở `urls_manage.py`, dưới `/manage/`) + service `imports` (dùng chung với lệnh `import_words`) + dịch vụ TTS/IPA.
- `games` — `GameType`, các module khuôn game, view chơi chung, chấm điểm + sao.
- `pronunciation` — luyện phát âm + ghi âm + gọi ASR + `Attempt`.
- `progress` — `GameResult`, `Reward`/`Badge`, màn tiến độ cho phụ huynh.

(Service `asr` đứng riêng ngoài Django — xem `CongNghe.md`.)
