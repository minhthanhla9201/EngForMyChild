/* ============================================================
   Khung JS dùng chung cho mỗi màn wireframe.
   - Chèn navbar mẫu (bé / quản lý / khách) vào placeholder.
   - Dựng thanh điều hướng đầu trang: về mục lục + màn trước/sau.
   Mỗi file màn khai báo <body data-screen="<id>"> để biết đang ở màn nào.
   ============================================================ */

// Thứ tự các màn (khớp danh sách trong index.html) để nút Trước/Sau hoạt động.
const WF_SCREENS = [
  { id: 'login',          file: 'login.html',          title: '0. Đăng nhập' },
  { id: 'kid-home',       file: 'kid-home.html',       title: 'Trang chủ khu bé (tiến độ)' },
  { id: 'learn-topics',   file: 'learn-topics.html',   title: 'Học: chọn chủ đề' },
  { id: 'learn-words',    file: 'learn-words.html',    title: 'Học: từ trong chủ đề' },
  { id: 'speak-choose',   file: 'speak-choose.html',   title: 'Phát âm: chọn bé & chủ đề' },
  { id: 'speak-practice', file: 'speak-practice.html', title: 'Phát âm: đọc theo & ghi âm' },
  { id: 'game-choose',    file: 'game-choose.html',    title: 'Trò chơi: chọn' },
  { id: 'game-listen',    file: 'game-listen.html',    title: 'Game: Nghe & chọn' },
  { id: 'game-match',     file: 'game-match.html',     title: 'Game: Lật thẻ tìm cặp' },
  { id: 'game-listen-image', file: 'game-listen-image.html', title: 'Game: Nghe & chọn hình' },
  { id: 'game-image-audio',  file: 'game-image-audio.html',  title: 'Game: Nhìn hình & chọn tiếng' },
  { id: 'game-match-image',  file: 'game-match-image.html',  title: 'Game: Ghép hình với tiếng' },
  { id: 'game-empty',     file: 'game-empty.html',     title: 'Game: chủ đề chưa đủ từ' },
  { id: 'pass-enter',     file: 'pass-enter.html',     title: 'Nhập passcode' },
  { id: 'pass-set',       file: 'pass-set.html',       title: 'Đặt passcode lần đầu' },
  { id: 'pass-change',    file: 'pass-change.html',    title: 'Đổi passcode' },
  { id: 'dashboard',      file: 'dashboard.html',      title: 'Bảng điều khiển' },
  { id: 'child-form',     file: 'child-form.html',     title: 'Thêm / sửa hồ sơ bé' },
  { id: 'topics',         file: 'topics.html',         title: 'Quản lý chủ đề' },
  { id: 'words',          file: 'words.html',          title: 'Quản lý từ vựng' },
  { id: 'wordform',       file: 'wordform.html',       title: 'Form thêm/sửa từ' },
  { id: 'import',         file: 'import.html',         title: 'Nhập CSV' },
  { id: 'progress',       file: 'progress.html',       title: 'Tiến độ của bé' },
];

// HTML 3 loại navbar mẫu (giống base_kid / base_manage / login chưa đăng nhập của app thật).
const WF_NAVS = {
  kid: `
  <nav class="navbar navbar-expand-lg navbar-brand-bar">
    <div class="container">
      <a class="navbar-brand fw-bold" href="#">🦜 Bé học tiếng Anh</a>
      <div class="navbar-collapse collapse show">
        <ul class="navbar-nav me-auto">
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-book"></i> Học từ vựng</a></li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-mic-fill"></i> Luyện phát âm</a></li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-controller"></i> Trò chơi</a></li>
        </ul>
        <ul class="navbar-nav align-items-lg-center">
          <li class="nav-item theme-picker me-lg-2">
            <button type="button" class="theme-toggle" title="Đổi màu">🎨</button>
            <div class="theme-menu">
              <button type="button" class="theme-swatch sw-candy active" title="Kẹo ngọt"></button>
              <button type="button" class="theme-swatch sw-ocean" title="Biển & trời"></button>
              <button type="button" class="theme-swatch sw-garden" title="Vườn cổ tích"></button>
            </div>
          </li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-shield-lock"></i> 👨‍👩‍👧 Cho phụ huynh</a></li>
        </ul>
      </div>
    </div>
  </nav>`,
  manage: `
  <nav class="navbar navbar-expand-lg wf-nav-manage">
    <div class="container">
      <a class="navbar-brand fw-bold" href="#"><i class="bi bi-gear-fill"></i> Khu quản lý</a>
      <div class="navbar-collapse collapse show">
        <ul class="navbar-nav me-auto">
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-speedometer2"></i> Bảng điều khiển</a></li>
          <li class="nav-item dropdown"><a class="nav-link dropdown-toggle" href="#"><i class="bi bi-list-ul"></i> Nội dung</a></li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-graph-up"></i> Tiến độ</a></li>
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-key"></i> Đổi passcode</a></li>
        </ul>
        <ul class="navbar-nav align-items-lg-center gap-lg-2">
          <li class="nav-item"><a class="nav-link" href="#"><i class="bi bi-arrow-left"></i> Về khu của bé</a></li>
          <li class="nav-item d-flex align-items-center gap-2">
            <span class="small text-white-50">phuhuynh</span>
            <button class="btn btn-sm btn-light"><i class="bi bi-box-arrow-right"></i> Thoát</button>
          </li>
        </ul>
      </div>
    </div>
  </nav>`,
  guest: `
  <nav class="navbar navbar-expand-lg navbar-brand-bar">
    <div class="container">
      <a class="navbar-brand fw-bold" href="#">🦜 Bé học tiếng Anh</a>
    </div>
  </nav>`,
};

document.addEventListener('DOMContentLoaded', () => {
  // 1) Chèn navbar mẫu vào placeholder của màn.
  const fill = (sel, html) => document.querySelectorAll(sel).forEach(el => el.innerHTML = html);
  fill('.wf-nav-kid', WF_NAVS.kid);
  fill('.wf-nav-mng', WF_NAVS.manage);
  fill('.wf-nav-guest', WF_NAVS.guest);

  // 2) Dựng thanh điều hướng wireframe đầu trang (về mục lục + trước/sau).
  const id = document.body.dataset.screen;
  const i = WF_SCREENS.findIndex(s => s.id === id);
  const prev = i > 0 ? WF_SCREENS[i - 1] : null;
  const next = i >= 0 && i < WF_SCREENS.length - 1 ? WF_SCREENS[i + 1] : null;
  const bar = document.getElementById('wf-bar');
  if (bar) {
    bar.innerHTML = `
      <div class="container d-flex align-items-center gap-3 py-2">
        <a href="index.html"><i class="bi bi-grid"></i> Mục lục</a>
        <span class="wf-title ms-auto">${i + 1}/${WF_SCREENS.length} — ${i >= 0 ? WF_SCREENS[i].title : ''}</span>
        <span class="ms-auto"></span>
        ${prev ? `<a href="${prev.file}">‹ ${prev.title}</a>` : '<span class="text-secondary">‹ đầu</span>'}
        ${next ? `<a href="${next.file}">${next.title} ›</a>` : '<span class="text-secondary">cuối ›</span>'}
      </div>`;
  }
});
