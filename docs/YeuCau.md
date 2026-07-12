# Yêu cầu — EngForMyChild

## 1. Mục tiêu
Website **học tiếng Anh chạy local** cho **bé 6–7 tuổi**, giúp bé làm quen tiếng Anh một cách vui vẻ qua trò chơi. Ưu tiên theo thứ tự: **Phát âm → Từ vựng → Ngữ pháp**. Dữ liệu (từ vựng, bản ghi luyện tập của bé) được **thu thập dần vào local**.

## 2. Đối tượng & nguyên tắc thiết kế cho trẻ
- **Bé 6–7 tuổi**, đọc chữ chưa thạo → **ít chữ, nhiều hình & âm thanh**; nút to, icon rõ, màu tươi.
- Mọi thao tác quan trọng có **biểu tượng + audio hướng dẫn**, không bắt bé đọc nhiều.
- **Vòng lặp ngắn, thưởng ngay:** mỗi hoạt động 30–60 giây; làm đúng có sao ⭐ / âm thanh vui.
- **Không phạt, không áp lực:** sai thì "Nghe lại nào!", không trừ điểm, không xếp hạng gây căng thẳng.
- **Có người lớn đi cùng:** khu vực riêng cho phụ huynh (xem tiến độ, thêm từ vựng, nghe lại bản ghi).
- **Ngôn ngữ giao diện:** **tiếng Việt + Anh song song** — hướng dẫn tiếng Việt cho bé dễ hiểu, nội dung học bằng tiếng Anh.

## 3. Vai trò người dùng
- **Bé (người học):** chọn chủ đề, chơi game, luyện phát âm. Không cần đăng nhập phức tạp (chọn avatar/hồ sơ).
- **Phụ huynh (quản trị nội dung):** đăng nhập, tạo hồ sơ bé, thêm/sửa từ vựng, xem tiến độ, nghe lại bản ghi của bé.

### 3.1. Tách 2 khu & lối vào khu quản lý
- Giao diện tách rõ **Khu của bé** (layout `base_kid`, navbar xanh) và **Khu quản lý** (layout `base_manage`, navbar xám, URL dưới `/manage/`). Chung một lần đăng nhập.
- **Đăng nhập** dùng cho cả 2 khu; phiên sống lâu (mặc định 30 ngày, trượt hạn — `SESSION_DAYS`).
- **Khu quản lý có lớp khoá thứ 2 = passcode** (`ManagePasscode`, lưu hash): bé không tự vào nghịch. Nhập đúng → mở khoá trong `MANAGE_UNLOCK_MINUTES` phút (mặc định 30, trượt hạn). Lần đầu chưa có passcode → buộc đặt; có màn đổi passcode trong khu quản lý.

## 4. Tính năng theo module

### 4.1. Phát âm (ưu tiên 1)
- Hiện **hình + từ tiếng Anh + nghĩa tiếng Việt + IPA**.
- Bé bấm 🔊 **nghe mẫu** (TTS hoặc file thu sẵn).
- Bé bấm 🎤 **thu giọng** → gửi sang service ASR (faster-whisper) → so khớp với từ đích → cho **sao** + animation vui. Sai thì khuyến khích nghe lại, **không trừ điểm**.
- Mỗi lần luyện lưu một bản ghi **`Attempt`** (audio bé + text ASR + điểm) → dữ liệu tích luỹ.
- **Độ thành thạo (4 level):** Chưa học → Đang học → Gần đạt → Thành thạo. Tính từ Attempt (không farm được). Hiển thị badge + sort ưu tiên từ mới.
- Game đại diện: **"Nhại con vẹt" 🦜** — nghe và lặp lại để vẹt vỗ tay.

### 4.2. Từ vựng (ưu tiên 2)
- Học theo **chủ đề** (Animals, Colors, Family, Food…), mỗi từ có hình + audio + nghĩa.
- Trò chơi dùng chung kho từ (xem `ThietKeDuLieu.md` mục Game):
  - **Nghe & chọn hình:** nghe audio → chọn đúng hình trong 4 lựa chọn.
  - **Nối hình ↔ từ.**
  - **Lật thẻ tìm cặp (memory).**
- Mỗi ván chơi lưu **`GameResult`** (số sao, thời gian) → tiến độ.

### 4.3. Ngữ pháp (ưu tiên 3 — giai đoạn sau)
- Mẫu câu đơn giản theo chủ đề đã học (vd "I see a cat").
- Game: **kéo–thả xếp câu**, **chọn a/an/the**.

### 4.4. Hệ thống thưởng (xuyên suốt)
- **Sao ⭐, huy hiệu, mở khoá dần** — tạo động lực quay lại.
  - **Tổng sao** = game_stars + speech_stars (mastery-based: thành thạo×3 + gần đạt×2 + đang học×1).
  - **Linh vật lớn dần** 🌱→🌿→🪴→🌳→🌸→🌟 theo tổng sao (bảng `PetStage`).
  - **Huy hiệu** tự động mở khi đạt ngưỡng (tổng sao, số ván, số lần luyện, chuỗi ngày).
  - Trang chủ hiển thị tách: **🎮 game / 🎤 phát âm** để bé thấy rõ tiến bộ.

### 4.5. Khu phụ huynh
- Đăng nhập; tạo/sửa **hồ sơ bé**.
- **Thêm từ vựng:** form trong app **và** import hàng loạt từ **CSV** (1 lệnh `manage.py import_words`), audio + IPA **tự sinh**.
- **Xem tiến độ:** bé học chủ đề nào, bao nhiêu sao, nghe lại bản ghi âm. Có phân trang + thời gian.
- **Tạo lại media:** khi mất file (xoá nhầm), dùng lệnh `recreate_media` + `fetch_images` + `gen_praise`.
- **Gen lại hình từng từ:** nút "Gen lại hình" ở form sửa từ (tải SVG emoji từ CDN).

## 5. Quản lý nội dung — "thu thập dữ liệu dần vào local"
- 4 cách nhập từ vựng (dễ → tự động): **CSV import** · **Django Admin** · **form phụ huynh trong app** · (audio/IPA **tự sinh** không cần thao tác tay).
- Audio TTS sinh **một lần** rồi **cache** vào `media/`; có thể thay bằng file thu thật cho từ quan trọng.
- Bản ghi luyện tập của bé (`Attempt`) và kết quả game (`GameResult`) lưu local, giữ qua các lần rebuild (volume Docker).

## 6. Phi chức năng
- **Chạy local**, miễn phí, mã nguồn mở (xem `CongNghe.md`).
- **Khi học không cần internet** (audio đã cache, ASR chạy local).
- **Riêng tư:** giọng bé không gửi ra ngoài — ASR xử lý cục bộ.
- Đóng gói **Docker**; dữ liệu (DB + media) gắn volume để không mất.
- Có **test** cho mỗi view; tài liệu (`docs/`) luôn khớp code.

## 7. Ngoài phạm vi (hiện tại)
- Không tài khoản online / đồng bộ đám mây.
- Không nhiều ngôn ngữ đích (chỉ tiếng Anh).
- Không bảng xếp hạng cạnh tranh giữa các bé.

## 8. Lộ trình (giai đoạn)
- **GĐ 0 (XONG):** Khung Django + Docker (`web`), `core` (AuditedModel, mixin), `base.html` thân thiện trẻ, `accounts` + `ChildProfile`.
- **GĐ 1 (XONG):** `catalog` (Topic/Word/AudioClip), import CSV + sinh IPA (eng-to-ipa) + audio (edge-tts ưu tiên, dự phòng pyttsx3 offline, có cache), trang xem từ vựng + nghe mẫu (Alpine.js).
- **GĐ 2 (XONG):** `pronunciation` — nghe mẫu + ghi âm trình duyệt (MediaRecorder + Alpine.js), lưu `Attempt` (chưa chấm điểm).
- **GĐ 3 (XONG):** Container `asr` (faster-whisper) + chấm điểm → sao + độ thành thạo.
- **GĐ 4 (XONG):** `games` — 5 game (Nghe & chọn, Lật thẻ, Nghe & chọn hình, Nhìn hình & chọn tiếng, Ghép hình với tiếng). Chấm sao + lưu `GameResult`.
- **GĐ 5 (XONG):** Huy hiệu + linh vật lớn dần + tiến độ phụ huynh hoàn chỉnh + độ thành thạo.
- **GĐ 6 (CHƯA):** Câu đơn ngắn theo chủ đề (Sentence model) + luyện phát âm cả câu (ASR mức câu). Chấm sao + độ thành thạo tương tự phát âm từ.
