# Wireframe — Bé học tiếng Anh

Bản xem trước giao diện (wireframe) **độc lập** với mã nguồn web.

## Cách xem
Nhấp đúp **`index.html`** để mở trong trình duyệt — **không cần chạy server, không cần internet**.

## Đặc điểm
- Tự chứa: mọi asset (Bootstrap, Bootstrap Icons, HTMX, Alpine.js, `style.css`) nằm trong `assets/` cạnh file này → chạy offline hoàn toàn.
- Dùng đúng `style.css` của app nên bố cục khớp với giao diện thật.
- Hiển thị **tất cả màn** kèm dữ liệu mẫu, gom theo nhóm (mục lục dính ở đầu trang) để dễ xác nhận trước khi code/đổi giao diện:

  **🔑 Đăng nhập**
  0. Đăng nhập (phụ huynh)

  **🧒 Khu của bé**
  - Học từ vựng — chọn chủ đề
  - Học từ vựng — từ trong chủ đề (nút 🔊 Nghe)
  - Luyện phát âm — chọn bé & chủ đề
  - Luyện phát âm — đọc theo & ghi âm
  - Trò chơi — chọn bé, game & chủ đề
  - Game: Nghe & chọn
  - Game: Lật thẻ tìm cặp (+ màn kết quả ⭐)
  - Game: chủ đề chưa đủ từ

  **⚙️ Khu quản lý (phụ huynh)**
  - Bảng điều khiển (tách Khu của bé / Khu quản lý)
  - Thêm / sửa hồ sơ bé
  - Quản lý chủ đề
  - Quản lý từ vựng (lọc + tìm + phân trang)
  - Form thêm/sửa từ
  - Nhập CSV
  - Tiến độ của bé

> Các màn động (game, luyện phát âm) hiển thị ở **một trạng thái đại diện** (đang chơi/đã ghi âm) để xem bố cục — wireframe là bản tĩnh, không chạy logic Alpine/JS thật.

## Đồng bộ giao diện
Wireframe chỉ là bản tĩnh để xem trước, **không** được app dùng khi chạy. Khi đổi `web/static/css/style.css`
hoặc nâng phiên bản thư viện trong `web/static/vendor/`, hãy copy lại sang `wireframe/assets/`
để wireframe khớp với giao diện thật:

```powershell
Copy-Item web\static\css\style.css wireframe\assets\style.css -Force
Copy-Item web\static\vendor\* wireframe\assets\vendor\ -Recurse -Force
```
