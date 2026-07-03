/*
 * kidTheme — chọn theme màu cho khu của bé, lưu trong localStorage (theo máy).
 *
 * Vì sao localStorage: web chạy local 1 máy, theme là sở thích hiển thị — không cần
 * lưu DB theo bé. Không có theme thì dùng mặc định (Kẹo ngọt) ở :root.
 *
 * FOUC (nháy màu): class theme được gắn SỚM bằng script inline trong <head>
 * (base_kid.html) trước khi CSS vẽ; file này chỉ lo nút chọn + lưu lựa chọn.
 */
(function () {
  'use strict';

  var KEY = 'kid-theme';
  // Danh sách theme: giá trị localStorage → class body ('' = mặc định :root).
  var THEMES = ['candy', 'ocean', 'garden'];
  var CLASS = { candy: '', ocean: 'theme-ocean', garden: 'theme-garden' };

  function current() {
    var t = localStorage.getItem(KEY);
    return THEMES.indexOf(t) >= 0 ? t : 'candy';
  }

  // Gắn class theme lên <body> (gỡ class theme cũ trước). Dùng chung với script <head>.
  function apply(theme) {
    var body = document.body;
    body.classList.remove('theme-ocean', 'theme-garden');
    if (CLASS[theme]) body.classList.add(CLASS[theme]);
  }

  function select(theme) {
    if (THEMES.indexOf(theme) < 0) return;
    localStorage.setItem(KEY, theme);
    apply(theme);
    markActive(theme);
  }

  function markActive(theme) {
    document.querySelectorAll('.theme-swatch').forEach(function (el) {
      el.classList.toggle('active', el.dataset.theme === theme);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    apply(current());          // đảm bảo khớp (phòng khi <head> chưa gắn)
    markActive(current());

    var toggle = document.getElementById('theme-toggle');
    var menu = document.getElementById('theme-menu');
    if (toggle && menu) {
      toggle.addEventListener('click', function (e) {
        e.stopPropagation();
        menu.classList.toggle('open');
      });
      menu.querySelectorAll('.theme-swatch').forEach(function (sw) {
        sw.addEventListener('click', function () {
          select(sw.dataset.theme);
          menu.classList.remove('open');
        });
      });
      // Bấm ra ngoài → đóng bảng chọn.
      document.addEventListener('click', function () { menu.classList.remove('open'); });
    }
  });
})();
