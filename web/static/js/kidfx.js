/*
 * kidFx — hiệu ứng khích lệ dùng chung cho khu của bé (offline).
 *
 * Vì sao viết lại: bản cũ dùng oscillator (tiếng "tin tin" điện tử) và
 * speechSynthesis (giọng OS đọc tiếng Việt rất tệ). Bản này dùng:
 *   - Âm thanh: file WAV chất lượng đã sinh sẵn (static/sfx/*.wav — lệnh gen_sfx).
 *   - Giọng động viên: mp3 tiếng Việt Neural sinh bằng edge-tts (lệnh gen_praise),
 *     client lấy danh sách qua API /learn/praise/manifest/ rồi bốc ngẫu nhiên.
 * Cả hai đều offline sau khi đã sinh. Nếu thiếu file → tự bỏ qua phần đó, hiệu
 * ứng hình (confetti + emoji) vẫn chạy.
 *
 * Dùng:
 *   kidFx.correct()  kidFx.wrong()  kidFx.cheer()
 *
 * Cấu hình URL (đặt trước khi nạp file này, không bắt buộc):
 *   window.KIDFX = { sfxBase: '/static/sfx/', praiseManifestUrl: '/learn/praise/manifest/' }
 */
(function () {
  'use strict';

  var CFG = window.KIDFX || {};
  var SFX_BASE = CFG.sfxBase || '/static/sfx/';
  var MANIFEST_URL = CFG.praiseManifestUrl || '/learn/praise/manifest/';

  var POP_EMOJI = ['🎉', '👏', '⭐', '🌟', '😄', '🥳', '✨'];

  function pick(arr) {
    return arr && arr.length ? arr[Math.floor(Math.random() * arr.length)] : null;
  }

  // ---------- Âm thanh hiệu ứng: preload file WAV, phát bằng cách clone ----------
  // Clone để phát chồng được (bé bấm nhanh liên tiếp) mà không cắt tiếng trước.
  var sfx = {};
  function loadSfx(name) {
    if (sfx[name]) return;
    var a = new Audio(SFX_BASE + name + '.wav');
    a.preload = 'auto';
    a.volume = 0.7;
    sfx[name] = a;
  }
  function playSfx(name) {
    var base = sfx[name];
    if (!base) return;
    try {
      var a = base.cloneNode();
      a.volume = base.volume;
      a.play().catch(function () {});  // trình duyệt chặn autoplay → im lặng
    } catch (e) {}
  }

  // ---------- Giọng động viên: mp3 tiếng Việt (edge-tts), lấy manifest 1 lần ----------
  var praise = { correct: [], wrong: [], cheer: [] };
  var praiseAudio = new Audio();
  praiseAudio.volume = 1.0;

  function loadPraiseManifest() {
    fetch(MANIFEST_URL)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (d && d.ok && d.lines) praise = d.lines;
      })
      .catch(function () { /* chưa sinh giọng → bỏ qua, vẫn có âm + confetti */ });
  }

  function speakPraise(kind) {
    var url = pick(praise[kind]);
    if (!url) return;  // chưa sinh mp3 cho tình huống này
    try {
      praiseAudio.src = url;
      praiseAudio.currentTime = 0;
      praiseAudio.play().catch(function () {});
    } catch (e) {}
  }

  // ---------- Lớp phủ hiệu ứng hình (confetti + emoji) ----------
  var layer = null;
  function fxLayer() {
    if (layer) return layer;
    layer = document.createElement('div');
    layer.className = 'kidfx-layer';
    document.body.appendChild(layer);
    return layer;
  }

  var CONFETTI_COLORS = ['#ff595e', '#ffca3a', '#8ac926', '#1982c4', '#6a4c93', '#ff924c'];

  function confetti(count) {
    var L = fxLayer();
    for (var i = 0; i < count; i++) {
      var p = document.createElement('span');
      p.className = 'kidfx-confetti';
      p.style.left = (Math.random() * 100) + 'vw';
      p.style.background = pick(CONFETTI_COLORS);
      p.style.animationDelay = (Math.random() * 0.2) + 's';
      p.style.animationDuration = (1.2 + Math.random() * 0.8) + 's';
      L.appendChild(p);
      (function (el) { setTimeout(function () { el.remove(); }, 2200); })(p);
    }
  }

  function popEmoji(emoji, cls) {
    var L = fxLayer();
    var box = document.createElement('div');
    box.className = 'kidfx-pop ' + (cls || '');
    box.innerHTML = '<span class="kidfx-pop-emoji">' + emoji + '</span>';
    L.appendChild(box);
    setTimeout(function () { box.remove(); }, 1400);
  }

  // Audio riêng cho câu hướng dẫn (không đè giọng động viên/từ vựng).
  var hintAudio = new Audio();
  hintAudio.volume = 1.0;

  // ================== API công khai ==================
  var kidFx = {
    // Phát giọng đọc câu hướng dẫn khi vào màn chơi (url mp3 do server sinh sẵn).
    // Rỗng/không có file → bỏ qua (chữ hướng dẫn vẫn hiển thị trong màn).
    playHint: function (url) {
      if (!url) return;
      try {
        hintAudio.src = url;
        hintAudio.currentTime = 0;
        hintAudio.play().catch(function () {});
      } catch (e) {}
    },
    correct: function () {
      confetti(28);
      popEmoji(pick(POP_EMOJI), 'kidfx-good');
      playSfx('correct');
      speakPraise('correct');
    },
    wrong: function () {
      popEmoji('🙂', 'kidfx-soft');
      playSfx('wrong');
      speakPraise('wrong');
    },
    cheer: function () {
      confetti(60);
      popEmoji('🏆', 'kidfx-good');
      playSfx('cheer');
      speakPraise('cheer');
    },
    // Hiện các huy hiệu VỪA mở khoá, lần lượt (list: [{icon, name_vi, desc_vi, voice_url}]).
    // Mỗi huy hiệu: banner giữa màn + confetti + đọc lời khen bằng GIỌNG NAM edge-tts
    // (voice_url — khác giọng động viên game). Thiếu mp3 thì bỏ qua giọng, vẫn có banner.
    badges: function (list) {
      if (!list || !list.length) return;
      list.forEach(function (b, i) {
        setTimeout(function () {
          showBadge(b);
          confetti(24);
          playSfx('cheer');
          if (b.voice_url) {
            try {
              var a = new Audio(b.voice_url);
              a.play().catch(function () {});
            } catch (e) {}
          }
        }, i * 2200);  // cách nhau để bé kịp xem từng cái
      });
    },
  };

  // Banner huy hiệu mới giữa màn (tự biến mất).
  function showBadge(b) {
    var L = fxLayer();
    var box = document.createElement('div');
    box.className = 'kidfx-badge';
    box.innerHTML =
      '<div class="kidfx-badge-title">🎉 Huy hiệu mới!</div>' +
      '<div class="kidfx-badge-icon">' + (b.icon || '🏅') + '</div>' +
      '<div class="kidfx-badge-name">' + (b.name_vi || '') + '</div>' +
      (b.desc_vi ? '<div class="kidfx-badge-desc">' + b.desc_vi + '</div>' : '');
    L.appendChild(box);
    setTimeout(function () { box.remove(); }, 2100);
  }

  // Preload âm thanh + tải manifest giọng ngay khi có thể.
  function init() {
    loadSfx('correct'); loadSfx('wrong'); loadSfx('cheer');
    loadPraiseManifest();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else { init(); }

  window.kidFx = kidFx;
})();
