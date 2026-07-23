# Công nghệ — EngForMyChild

> Website **học tiếng Anh chạy local cho bé 6–7 tuổi**. Tập trung: **Phát âm → Từ vựng → Ngữ pháp**, tất cả bọc trong **trò chơi**. Dữ liệu (từ vựng, bản ghi của bé) **thu thập dần vào local**.

## 1. Nguyên tắc chọn công nghệ
- **Miễn phí & mã nguồn mở** toàn bộ. Không phụ thuộc dịch vụ trả phí.
- **Chạy local**, một máy là đủ; đóng gói bằng **Docker** để bật/tắt gọn.
- **Server-rendered, KHÔNG SPA.** Trang do Django render; tương tác động dùng **HTMX** + **Alpine.js** (đủ cho game đơn giản, nhẹ, dễ bảo trì).
- **Dữ liệu tách rời code:** thêm từ vựng / trò chơi qua dữ liệu + cấu hình, hạn chế sửa code (xem `ThietKeDuLieu.md`).
- **Offline-first cho lúc học:** audio sinh sẵn và cache vào `media/`; khi bé học không cần internet. Internet chỉ cần lúc *sinh* audio TTS lần đầu.

## 2. Stack chính

| Lớp | Công nghệ | Phiên bản | Vì sao |
|---|---|---|---|
| Ngôn ngữ | Python | 3.14 | Phiên bản mới nhất, nhiều thư viện audio/ASR |
| Web framework | Django | 5.2 LTS (5.2.16) | ORM + Admin (nhập liệu nhanh) + template sẵn. Tương thích Python 3.14 |
| CSDL | SQLite (dev/local) → **MySQL 8** (về sau) | (kèm Python) / 8.x | Chạy local 1 máy bằng SQLite; **thiết kế để chuyển MySQL không sửa code** — chỉ đổi `DATABASE_URL` (xem `ThietKeDuLieu.md` mục 0.1) |
| Template | Django Templates | — | Server-rendered |
| CSS | Bootstrap | 5 | Bố cục nhanh, responsive, miễn phí |
| Icon | Bootstrap Icons | — | Bé cần nhiều icon to, rõ |
| Tương tác nhẹ | **HTMX** | 1.x | Cập nhật từng mảnh trang không cần viết nhiều JS |
| Tương tác client | **Alpine.js** | 3.x | Trạng thái nhỏ phía client cho game (lật thẻ, đếm giờ, kéo–thả) — nhẹ ~15KB, không build tool |
| Ghi âm | Web Audio API (`MediaRecorder`) | trình duyệt | Thu giọng bé, không cài thêm gì |
| Hiệu ứng khích lệ | `static/js/kidfx.js` (thuần) | — | Khi bé làm đúng/sai: confetti + emoji nảy (CSS), **âm thanh WAV** (file sinh sẵn `static/sfx/*.wav` — lệnh `gen_sfx`), **giọng động viên tiếng Việt** (mp3 Neural do edge-tts sinh — lệnh `gen_praise`, lấy qua API `praise/manifest/`). Offline sau khi sinh, không thư viện ngoài. Dùng chung: `kidFx.correct()/wrong()/cheer()/badges()` — nạp cuối `base.html`, gọi từ game/phát âm |
| Giọng theo ngữ cảnh | edge-tts, 2 giọng | — | Lời động viên game dùng giọng **nữ** (`TTS_VOICE_VI`, mặc định `vi-VN-HoaiMyNeural`); lời khen khi mở **huy hiệu** dùng giọng **nam** (`TTS_VOICE_BADGE`, mặc định `vi-VN-NamMinhNeural`) — bé thấy khoảnh khắc mở huy hiệu "đặc biệt" hơn. Cùng câu + giọng khác → file mp3 khác (hash gồm giọng). Cả hai sinh bằng `gen_praise` |
| Chọn theme màu | `static/js/kidtheme.js` (thuần) | — | Khu bé có nút 🎨 trên navbar → 3 theme (Kẹo ngọt / Biển & trời / Vườn cổ tích). Mỗi theme là 1 bộ biến CSS đầy đủ (`:root` + `body.theme-ocean`/`.theme-garden`), lưu lựa chọn trong `localStorage` (theo máy, không đụng DB). Offline. Thêm theme = 1 khối biến + 1 ô màu (xem memory/skill) |
| Giọng hướng dẫn game | edge-tts (giọng nữ) | — | Câu hướng dẫn lưu ở `GameType.hint_vi`; sinh mp3 qua `gen_praise` (giọng `TTS_VOICE_VI`), tự đọc 1 lần khi bé vào màn chơi (`kidFx.playHint`, URL từ `praise.hint_voice_url`). Bé chưa biết chữ nghe hiểu cách chơi |

## 3. Audio (phát âm mẫu) — miễn phí, offline khi học
- **TTS sinh tự động:** [`edge-tts`](https://github.com/rany2/edge-tts) — giọng Microsoft Neural chất lượng cao, **miễn phí**. Cần internet *lúc sinh*; sinh xong **cache mp3 vào `media/audio/`**, sau đó học offline.
  - Dự phòng hoàn toàn offline: `pyttsx3` (đọc bằng giọng hệ điều hành — chất lượng thấp hơn, dùng khi không có net).
- **File thu sẵn (tuỳ chọn):** với từ quan trọng, có thể upload mp3 thu thật để thay TTS (model `AudioClip` cho phép nhiều nguồn/từ — xem `ThietKeDuLieu.md`).
- **Phiên âm IPA tự động:** [`eng-to-ipa`](https://pypi.org/project/eng-to-ipa/) — sinh IPA từ từ tiếng Anh, khỏi tra tay.

## 4. Chấm phát âm (ASR) — service riêng trong Docker (GĐ 3 — ĐÃ LÀM)
- **[`faster-whisper`](https://github.com/SYSTRAN/faster-whisper)** — bản tối ưu của Whisper (OpenAI), **miễn phí, chạy local, không gửi dữ liệu ra ngoài**. Chấm "bé đọc có đúng từ đích không" ở **mức từ**.
- Đặt trong **container `asr` riêng** (`asr/`: FastAPI + uvicorn + ffmpeg). Endpoint tối giản `POST /transcribe` (nhận file audio → trả text nghe được) + `GET /health`. **Service chỉ NHẬN DẠNG; việc SO KHỚP + quy sao nằm ở web** (`pronunciation/asr.py`) — dễ test/chỉnh, service nhẹ.
  - **Vì sao tách:** model Whisper nặng, khởi động chậm. Tách container giúp web nhẹ, bật/tắt ASR độc lập.
- **Cách chạy:** web chạy LOCAL (`runserver`), chỉ ASR trong Docker → `docker compose up asr`. Web gọi qua `ASR_URL` (mặc định `http://localhost:9002` — container nghe 9000, publish ra host 9002; nếu web cũng trong Docker thì `http://asr:9000`). Model cache ở volume `asr_models` (không tải lại).
- **Model mặc định:** `base` (env `ASR_MODEL`; đổi `tiny`/`small` được), CPU int8, ngôn ngữ `en`.
- **Chấm điểm:** `pronunciation/asr.py` chuẩn hoá + so khớp chuỗi (`difflib.SequenceMatcher`) giữa text ASR và từ đích → điểm 0–100 → **sao 0–3** (ngưỡng khích lệ 85/60/35, nới hơn game). Sai → hiện "máy nghe thành X" + tự phát mẫu + nút Thử lại. **ASR tắt/timeout → vẫn lưu bản ghi, báo "chưa chấm được" (không 500).** Giọng bé chỉ tới service local.

## 5. Đóng gói — Docker Compose

```
docker-compose.yml
├─ web   : Django + Gunicorn (hoặc runserver khi dev)   port 8000
└─ asr   : faster-whisper + FastAPI                       port 9000 (nội bộ)
```

- Volume gắn `media/` (audio cache + bản ghi của bé) và `db.sqlite3` ra ngoài host → **dữ liệu thu thập được giữ lại** khi rebuild container.
- Model Whisper tải vào volume riêng (`asr_models`) để không tải lại mỗi lần build.
- `.env` chứa cấu hình: `DEBUG`, `SECRET_KEY`, `DATABASE_URL`, `ASR_URL`, `TTS_VOICE`, `LOG_LEVEL`...
- **Chuyển MySQL về sau (không sửa code):** thêm service `db` (MySQL 8, `utf8mb4`) + volume, cài `mysqlclient` trong Dockerfile `web`, đổi `DATABASE_URL` sang `mysql://...`, rồi `migrate` + nạp lại dữ liệu. Schema do Django migrations sinh ra nên chạy được trên cả SQLite lẫn MySQL.
- Dev có thể chạy không Docker (venv + `runserver`); Docker dùng khi muốn chạy "một phát" hoặc bật kèm ASR.

## 6. Thư viện Python dự kiến
- `django`, `python-dotenv`, `dj-database-url` (đọc `DATABASE_URL`), `mysqlclient` (chỉ cần khi chạy MySQL)
- `edge-tts` (TTS), `eng-to-ipa` (IPA), `pyttsx3` (TTS offline dự phòng)
- Phía `asr`: `faster-whisper`, `fastapi`, `uvicorn`, `python-multipart`
- Dev/test: dùng `django.test` sẵn có (chưa cần pytest).

## 7. Những gì KHÔNG dùng (giữ đơn giản)
- Không React/Vue/SPA — thừa với nhu cầu này.
- Không Node build pipeline — Bootstrap/HTMX/Alpine nạp qua file tĩnh (CDN khi dev, hoặc tải về `static/` để offline).
- Không dịch vụ cloud trả phí (TTS/ASR đều chạy local).
