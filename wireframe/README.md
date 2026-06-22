# Wireframe — Bé học tiếng Anh

Bản xem trước giao diện (wireframe) **độc lập** với mã nguồn web.

## Cách xem
Nhấp đúp **`index.html`** (trang **mục lục**) → bấm thẻ để mở từng màn. Trong mỗi màn có thanh
trên cùng để **về mục lục** hoặc xem **màn trước/sau**. Không cần chạy server, không cần internet.

## Cấu trúc (mỗi màn 1 file)
- `index.html` — trang mục lục, liên kết tới 19 file màn.
- `<tên-màn>.html` — mỗi màn một file độc lập (vd `login.html`, `dashboard.html`, `pass-enter.html`...).
- `assets/` — asset dùng chung:
  - `vendor/` (Bootstrap, Bootstrap Icons, HTMX, Alpine.js) + `style.css` (CSS thật của app).
  - `wf-frame.css` — CSS khung wireframe (nhãn màn, viền "cửa sổ", nav xám...).
  - `wf-frame.js` — chèn navbar mẫu (bé / quản lý / khách) + dựng thanh điều hướng trước/sau.

> Khung (navbar mẫu, CSS, thanh điều hướng) nằm CHUNG trong `assets/wf-frame.*` → sửa 1 chỗ áp cho mọi màn,
> không lặp lại trong từng file. Mỗi file màn chỉ chứa nội dung màn + khai báo `<body data-screen="…">`.

## Đặc điểm
- Tự chứa: mọi asset nằm trong `assets/` cạnh các file → chạy offline hoàn toàn.
- Dùng đúng `style.css` của app nên bố cục khớp với giao diện thật.
- **Tất cả màn** kèm dữ liệu mẫu, gom theo nhóm (xem trong `index.html`):

  **🔑 Đăng nhập**
  0. Đăng nhập (phụ huynh) — phiên sống lâu (mặc định 30 ngày, trượt hạn)

  **🧒 Khu của bé** — navbar XANH; chỉ có Học/Phát âm/Trò chơi + nút nhỏ "👨‍👩‍👧 Cho phụ huynh"
  - Học từ vựng — chọn chủ đề
  - Học từ vựng — từ trong chủ đề (nút 🔊 Nghe)
  - Luyện phát âm — chọn bé & chủ đề
  - Luyện phát âm — đọc theo & ghi âm
  - Trò chơi — chọn bé, game & chủ đề
  - Game: Nghe & chọn
  - Game: Lật thẻ tìm cặp (+ màn kết quả ⭐)
  - Game: chủ đề chưa đủ từ

  **🔒 Vào khu quản lý (passcode)** — lớp khoá thứ 2 sau đăng nhập
  - Nhập passcode (mở khoá giữ 30' trượt hạn theo thao tác)
  - Đặt passcode lần đầu (khi DB chưa có)
  - Đổi passcode (trong khu quản lý)

  **⚙️ Khu quản lý (phụ huynh)** — navbar XÁM; tách hẳn khỏi khu của bé, có nút "← Về khu của bé"
  - Bảng điều khiển (số liệu + lối tắt CRUD + hồ sơ bé)
  - Thêm / sửa hồ sơ bé
  - Quản lý chủ đề
  - Quản lý từ vựng (lọc + tìm + phân trang)
  - Form thêm/sửa từ
  - Nhập CSV
  - Tiến độ của bé

> **Tách 2 khu (đã triển khai trong app):** khu của bé (nav xanh) và khu quản lý (nav xám) dùng 2 layout riêng (`base_kid.html` / `base_manage.html`), khu quản lý gom dưới tiền tố URL `/manage/` và cần passcode. Vẫn chung 1 lần đăng nhập.
>
> Các màn động (game, luyện phát âm) hiển thị ở **một trạng thái đại diện** (đang chơi/đã ghi âm) để xem bố cục — wireframe là bản tĩnh, không chạy logic Alpine/JS thật.

## Đồng bộ giao diện
Wireframe chỉ là bản tĩnh để xem trước, **không** được app dùng khi chạy. Khi đổi `web/static/css/style.css`
hoặc nâng phiên bản thư viện trong `web/static/vendor/`, hãy copy lại sang `wireframe/assets/`
để wireframe khớp với giao diện thật:

```powershell
Copy-Item web\static\css\style.css wireframe\assets\style.css -Force
Copy-Item web\static\vendor\* wireframe\assets\vendor\ -Recurse -Force
```
