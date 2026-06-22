# EngForMyChild — Web học tiếng Anh cho bé 🦜

Website chạy **trên máy của bạn** (local) giúp bé 6–7 tuổi học tiếng Anh: **phát âm → từ vựng → ngữ pháp**, qua trò chơi. Giao diện tiếng Việt + Anh.

> Tài liệu này viết cho người **chưa quen lập trình**. Cứ làm tuần tự từng bước, copy nguyên lệnh là chạy được.

---

## 1. Cần cài gì trước

Bạn chỉ cần **một trong hai** cách dưới đây:

- **Cách A — Không Docker** (đơn giản nhất để bắt đầu): cần **Python** (đã có sẵn trên máy bạn — bản 3.9).
- **Cách B — Docker** (giống môi trường triển khai thật): cần **Docker Desktop** (máy bạn đã cài).

Mở **PowerShell** để gõ lệnh: bấm phím `Windows`, gõ `powershell`, Enter.

Mọi lệnh dưới đây chạy từ thư mục dự án. Trước tiên vào đúng thư mục:

```powershell
cd e:\Thanhhm\Others\Learning\EngForMyChild
```

---

## 2. Cách A — Chạy trực tiếp bằng Python (khuyên dùng khi học/sửa)

Dự án đã được dựng sẵn (có thư mục `.venv` chứa Python + thư viện).

**Lần đầu tiên** (hoặc nếu thấy cảnh báo *"You have N unapplied migration(s)"*): tạo cơ sở dữ liệu một lần bằng:
```powershell
.\.venv\Scripts\python.exe web\manage.py migrate
```
Nếu chưa có tài khoản quản trị thì tạo (làm 1 lần, tự đặt mật khẩu khi được hỏi):
```powershell
.\.venv\Scripts\python.exe web\manage.py createsuperuser
```

**Mỗi lần muốn chạy web**, làm 1 lệnh:
```powershell
.\.venv\Scripts\python.exe web\manage.py runserver
```

Khi thấy dòng `Starting development server at http://127.0.0.1:8000/`, mở trình duyệt vào:

> **http://127.0.0.1:8000**

Đăng nhập bằng tài khoản quản trị đã tạo sẵn:

- Tên đăng nhập: **admin**
- Mật khẩu: **admin123**

Sau khi đăng nhập sẽ thấy **Bảng điều khiển**, chia rõ 2 khu:
- **🧒 Khu của bé** — vào Học từ vựng / Luyện phát âm / Trò chơi.
- **⚙️ Khu quản lý** (cho phụ huynh) — Hồ sơ bé, Chủ đề, Từ vựng, Nhập CSV, Tiến độ của bé.

Mọi việc quản lý làm ngay trong khu này (không cần vào `/admin`): bấm **Thêm bé**,
hoặc mở menu **⚙️ Quản lý** trên thanh trên cùng để thêm/sửa chủ đề, từ vựng,
nhập CSV, xem tiến độ của con.

**Dừng server:** quay lại cửa sổ PowerShell, bấm `Ctrl + C`.

### Trang quản trị nâng cao (Django Admin)
Khu quản lý trong app đã đủ cho việc thường ngày. Khi cần thao tác sâu hơn
(sửa từng bản ghi audio, dữ liệu hệ thống...), vẫn có thể vào:

> **http://127.0.0.1:8000/admin** — đăng nhập cùng tài khoản admin ở trên.

---

## 3. Cách B — Chạy bằng Docker

Dùng khi muốn chạy "một phát" giống môi trường thật, hoặc về sau bật kèm dịch vụ chấm phát âm.

**Bật:**
```powershell
docker compose up --build
```
Lần đầu sẽ tải/đóng gói nên hơi lâu. Khi xong, mở: **http://localhost:8000**

**Tắt:** bấm `Ctrl + C`, rồi:
```powershell
docker compose down
```

> Dữ liệu (cơ sở dữ liệu, file âm thanh) được giữ lại qua các lần chạy nhờ "volume" đã cấu hình sẵn — tắt/bật không mất.

---

## 4. Các việc thường làm (cheat-sheet)

Tất cả lệnh chạy từ thư mục gốc dự án, dùng Python trong `.venv`:

| Việc | Lệnh |
|---|---|
| Chạy web | `.\.venv\Scripts\python.exe web\manage.py runserver` |
| Tạo tài khoản quản trị mới | `.\.venv\Scripts\python.exe web\manage.py createsuperuser` |
| Đổi mật khẩu admin | `.\.venv\Scripts\python.exe web\manage.py changepassword admin` |
| Cập nhật cơ sở dữ liệu sau khi đổi cấu trúc | `.\.venv\Scripts\python.exe web\manage.py makemigrations` rồi `... migrate` |
| Kiểm tra cấu hình có lỗi không | `.\.venv\Scripts\python.exe web\manage.py check` |
| Chạy kiểm thử (test) | `.\.venv\Scripts\python.exe web\manage.py test core accounts catalog pronunciation games` |
| Nhập từ vựng từ file CSV | `.\.venv\Scripts\python.exe web\manage.py import_words web\sample_words.csv` |
| Nhập từ vựng KHÔNG cần mạng (không sinh audio) | `.\.venv\Scripts\python.exe web\manage.py import_words web\sample_words.csv --no-audio` |

### Nhập từ vựng (thu thập dữ liệu dần)
Tạo file CSV (mở bằng Excel/Google Sheet rồi lưu dạng CSV) với các cột:
```csv
topic,topic_vi,text_en,text_vi,level
Animals,Động vật,cat,con mèo,1
Colors,Màu sắc,red,màu đỏ,1
```
Có **2 cách nhập**:
1. **Qua web (dễ nhất):** menu **⚙️ Quản lý → Nhập từ CSV**, chọn file rồi bấm Nhập.
2. **Qua dòng lệnh:** chạy lệnh `import_words` (xem bảng trên).

Cả 2 cách dùng chung một bộ xử lý: tự tạo chủ đề, tự sinh phiên âm IPA và (tuỳ chọn) **tự sinh audio** cho từng từ.
- Thêm/sửa thủ công từng chủ đề, từng từ cũng làm ngay trong menu **⚙️ Quản lý**.
- File mẫu có sẵn: `web\sample_words.csv`.
- **Mạng yếu/không có mạng:** thêm `--no-audio` để chỉ nhập từ (audio sẽ được tạo sau, ngay khi bé bấm "Nghe" lần đầu — lúc đó cần mạng một lần; nếu vẫn không có mạng, hệ thống tự đọc bằng giọng máy của Windows).
- Chạy lại lệnh nhiều lần **không tạo trùng** (an toàn).

### Học từ vựng & nghe phát âm
Sau khi đăng nhập, bấm **Học từ vựng** ở trang chủ → chọn chủ đề → bấm 🔊 **Nghe** ở mỗi từ. Lần đầu nghe một từ, hệ thống sinh audio rồi lưu lại; các lần sau phát ngay.

### Luyện phát âm (ghi âm)
Bấm **Luyện phát âm** ở trang chủ → chọn bé → chọn chủ đề. Ở mỗi từ: bé bấm **Nghe mẫu**, rồi bấm **Thu giọng** để đọc theo (bấm lần nữa để dừng). Bản ghi được lưu lại; phụ huynh xem ở **⚙️ Quản lý → Tiến độ của bé** (chi tiết bản ghi xem trong Django Admin).
- **Lưu ý:** trình duyệt sẽ hỏi quyền dùng **micro** — hãy bấm Cho phép. Ghi âm chạy được trên `localhost` (Chrome/Edge/Firefox).
- Phần **chấm điểm tự động** (máy nghe bé đọc đúng chưa) sẽ có ở Giai đoạn 3 (dùng Faster-Whisper, cần Docker).

### Trò chơi
Bấm **Trò chơi** ở trang chủ → chọn bé → chọn game → chọn chủ đề. Hiện có:
- **Nghe & chọn** 👂 — nghe phát âm rồi chọn đúng từ trong 4 lựa chọn.
- **Lật thẻ tìm cặp** 🃏 — lật thẻ ghép cặp Anh ↔ Việt.

Chơi xong được thưởng **sao ⭐**, kết quả lưu lại để theo dõi tiến độ. Mỗi game cần chủ đề có **đủ số từ tối thiểu** (mặc định 4) — nếu thiếu, hãy nhập thêm từ vựng.
> Thêm trò chơi mới chỉ cần thêm 1 module trong `web/games/engine/` và 1 bản ghi `GameType` (không phải sửa màn hình chọn game).

### Chạy offline (không cần internet)
Toàn bộ thư viện giao diện (Bootstrap, Bootstrap Icons, HTMX, Alpine.js) đã được **tải sẵn** vào `web/static/vendor/` và nạp từ đó — **không gọi CDN**, nên giao diện chạy được khi không có mạng. Không cần làm gì thêm.

### Xem trước giao diện (wireframe)
Muốn xem nhanh bố cục các màn quản lý mà **không cần chạy server**: mở thẳng file
`wireframe/index.html` (thư mục `wireframe/` ở **gốc dự án**, độc lập với mã nguồn web) bằng trình duyệt (nhấp đúp).
Trang này tự chứa asset riêng, dùng đúng CSS thật, hiển thị 6 màn (Bảng điều khiển, Quản lý chủ đề, Quản lý từ vựng, Form thêm/sửa, Nhập CSV, Tiến độ) kèm dữ liệu mẫu để dễ xác nhận trước khi code/đổi giao diện.
Chi tiết & cách đồng bộ khi đổi `style.css`: xem `wireframe/README.md`.

---

## 5. Cấu hình (file `web\.env`)

Các thiết lập đổi theo máy nằm trong **`web\.env`** (đã tạo sẵn). Mở bằng Notepad để xem/sửa. Vài mục quan trọng:

- `DEBUG=True` — chế độ phát triển (hiện lỗi chi tiết). Khi chạy thật để `False`.
- `DATABASE_URL=sqlite:///db.sqlite3` — đang dùng **SQLite** (một file, không cần cài gì). Có thể đổi sang MySQL sau (xem mục 7).
- `TTS_VOICE`, `ASR_URL` — dùng cho phần phát âm ở giai đoạn sau.

> File `.env.example` là bản mẫu để tham khảo; **`.env`** mới là bản đang dùng thật.

---

## 6. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `python: command not found` hoặc không nhận lệnh | Dùng đúng đường dẫn `.\.venv\Scripts\python.exe ...` như trong tài liệu, đừng gõ `python` trơn. |
| Mở web báo *"That port is already in use"* | Đang có server chạy rồi. Đóng cửa sổ cũ, hoặc chạy cổng khác: thêm `8001` vào cuối lệnh runserver. |
| Quên mật khẩu admin | Đặt lại: `.\.venv\Scripts\python.exe web\manage.py changepassword admin` |
| Trang báo lỗi 400 / CSRF khi đăng nhập qua Docker | Kiểm tra `CSRF_TRUSTED_ORIGINS` trong `web\.env` có địa chỉ bạn đang mở (vd `http://localhost:8000`). |
| Docker báo không kết nối được | Mở **Docker Desktop** trước, đợi nó khởi động xong rồi mới chạy `docker compose up`. |

---

## 7. Chuyển sang MySQL về sau (khi cần)

Hiện dùng SQLite cho gọn. Khi muốn dùng MySQL, **không phải sửa code** — chỉ:
1. Bật service `db` (MySQL) trong `docker-compose.yml` (đã để sẵn, đang comment).
2. Mở `mysqlclient` trong `web\requirements.txt` và phần cài đặt trong `web\Dockerfile`.
3. Đổi dòng `DATABASE_URL` trong `web\.env` sang `mysql://...`.
4. Chạy lại `migrate`.

Chi tiết kỹ thuật: `docs/ThietKeDuLieu.md` mục **0.1**.

---

## 8. Tài liệu dự án

| File | Nội dung |
|---|---|
| `docs/YeuCau.md` | Yêu cầu, đối tượng, tính năng, lộ trình các giai đoạn |
| `docs/ThietKeDuLieu.md` | Mô hình dữ liệu + sơ đồ ERD + tương thích SQLite/MySQL |
| `docs/CongNghe.md` | Công nghệ sử dụng (đều miễn phí, mã nguồn mở) |

**Tình trạng hiện tại:** đã xong **GĐ 0** (khung + đăng nhập + hồ sơ bé), **GĐ 1** (từ vựng + nhập CSV + nghe mẫu), **GĐ 2** (luyện phát âm + ghi âm), **GĐ 4** (trò chơi: Nghe & chọn, Lật thẻ tìm cặp + chấm sao). Còn lại: **GĐ 3** (chấm điểm phát âm bằng Faster-Whisper — cần Docker) và **GĐ 5** (ngữ pháp + huy hiệu + trang tiến độ phụ huynh).

---

## 9. Tóm tắt nhanh nhất

```powershell
cd e:\Thanhhm\Others\Learning\EngForMyChild
.\.venv\Scripts\python.exe web\manage.py runserver
```
→ Mở **http://127.0.0.1:8000** → đăng nhập **admin / admin123**. Xong!
