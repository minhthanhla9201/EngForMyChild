/*
 * gameCommon — tiện ích dùng chung cho MỌI màn game của bé.
 *
 * Vì sao có file này: 5 template play_*.html trước đây copy nguyên văn cùng một
 * đoạn getCookie / đọc câu hướng dẫn / nộp ván chơi. Sửa luật ở một chỗ rất dễ
 * quên các chỗ còn lại. Gom về đây để mỗi template chỉ còn LUẬT CHƠI riêng.
 *
 * Dùng trong Alpine:
 *   const s = gameCommon.roundState();        // state chung (index, score, finished...)
 *   await gameCommon.submitRound(url, body, this);
 *
 * Phụ thuộc: kidFx (kidfx.js) — nếu thiếu thì tự bỏ qua hiệu ứng, game vẫn chạy.
 */
(function () {
  'use strict';

  /** Đọc cookie theo tên (lấy csrftoken cho POST). */
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }

  /** Đọc dữ liệu JSON do Django nhúng bằng {{ ...|json_script:"id" }}. */
  function readJson(elementId, fallback) {
    const el = document.getElementById(elementId);
    if (!el) return fallback;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return fallback;
    }
  }

  /**
   * Đọc câu hướng dẫn tiếng Việt 1 lần khi vào màn (bé chưa biết chữ → nghe hiểu).
   * Gọi ở đầu mỗi template game, sau khi json_script "hint-url" đã render.
   */
  function playHintOnLoad(elementId) {
    const url = readJson(elementId || 'hint-url', '');
    if (!url) return;
    window.addEventListener('load', function () {
      if (window.kidFx) kidFx.playHint(url);
    });
  }

  /** Quy số sao → chuỗi emoji. 0 sao vẫn hiện 🌱 để bé không thấy "trắng tay". */
  function starText(stars) {
    return '⭐'.repeat(stars || 0) || '🌱';
  }

  /** Phản hồi tức thì khi bé trả lời: đúng thì vui, sai thì nhẹ nhàng. */
  function feedback(correct) {
    if (!window.kidFx) return;
    correct ? kidFx.correct() : kidFx.wrong();
  }

  /**
   * Phát audio tiếng Anh của một từ (API catalog tự sinh + cache).
   * `audioEl` là phần tử <audio> (thường là this.$refs.player).
   *
   * Mẫu URL lấy từ window.GAME_CFG.wordAudioUrl ({{ '{id}' }} là chỗ thay id) để
   * template dựng bằng {% url %}; giữ mặc định cho trường hợp chưa khai báo.
   */
  function wordAudioUrl(wordId) {
    const pattern = (window.GAME_CFG || {}).wordAudioUrl || '/learn/word/{id}/audio/';
    return pattern.replace('{id}', wordId);
  }

  async function playWordAudio(wordId, audioEl) {
    if (!wordId || !audioEl) return;
    try {
      const r = await fetch(wordAudioUrl(wordId));
      const d = await r.json();
      if (d.ok) {
        audioEl.src = d.url;
        await audioEl.play();
      }
    } catch (e) { /* mất mạng/chưa có file → im lặng, bé bấm lại được */ }
  }

  /**
   * Phát mp3 đọc TÊN tiếng Việt của một hình ("con mèo").
   * Dùng player RIÊNG để không cắt ngang tiếng Anh đang phát.
   */
  function playViName(url, audioEl) {
    if (!url || !audioEl) return;
    try {
      audioEl.src = url;
      audioEl.currentTime = 0;
      audioEl.play().catch(function () {});
    } catch (e) { /* bỏ qua */ }
  }

  /**
   * Nộp kết quả ván chơi và cập nhật state kết thúc.
   *
   * `state` là object Alpine có sẵn các field starText/newBadges/finished —
   * hàm này ghi thẳng vào đó rồi reo mừng, nên template không phải lặp lại.
   * Lỗi mạng → vẫn kết thúc êm với 🌱, KHÔNG để bé kẹt màn.
   */
  async function submitRound(url, payload, state) {
    try {
      const r = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(payload),
      });
      const d = await r.json();
      state.starText = starText(d.stars);
      state.newBadges = d.badges || [];
    } catch (e) {
      state.starText = starText(0);
      state.newBadges = [];
    }
    state.finished = true;
    if (window.kidFx) {
      kidFx.cheer();
      kidFx.badges(state.newBadges);
    }
  }

  /** State chung của game dạng "trả lời từng câu" (nghe/nhìn rồi chọn). */
  function quizState() {
    return {
      questions: [], index: 0, answered: false, lastCorrect: false,
      score: 0, finished: false, answers: [], starText: '', newBadges: [],

      /** Nạp câu hỏi từ json_script "round-data". Không có câu nào → kết thúc luôn. */
      loadQuestions() {
        const data = readJson('round-data', {});
        this.questions = data.questions || [];
        if (!this.questions.length) this.finished = true;
      },

      /**
       * Câu hỏi hiện tại. Phải là METHOD, KHÔNG được là getter:
       * template dùng {...gameCommon.quizState()} mà spread không sao chép
       * getter — nó gọi getter 1 lần (lúc questions còn rỗng) rồi đóng băng
       * giá trị, khiến mọi câu hỏi biến mất. Đã từng gây lỗi trắng màn.
       */
      current() {
        return this.questions[this.index] || { choices: [] };
      },

      /**
       * Ghi nhận một câu trả lời: chấm đúng/sai, phản hồi, lưu lại để nộp.
       * Trả về true nếu đúng (template dùng nếu cần).
       */
      record(pickedId) {
        const answerId = this.current().answer_id;
        this.answered = true;
        this.lastCorrect = pickedId === answerId;
        if (this.lastCorrect) this.score++;
        feedback(this.lastCorrect);
        this.answers.push({ answer_id: answerId, picked_id: pickedId });
        return this.lastCorrect;
      },

      /**
       * Sang câu kế tiếp sau `delay` ms (để bé kịp thấy phản hồi), hoặc nộp bài
       * nếu đã là câu cuối. `onNext` là callback tuỳ chọn cho việc riêng của game.
       */
      advance(submitUrl, delay, onNext) {
        setTimeout(() => {
          if (this.index < this.questions.length - 1) {
            this.index++;
            this.answered = false;
            if (onNext) onNext.call(this);
          } else {
            submitRound(submitUrl, { answers: this.answers }, this);
          }
        }, delay || 900);
      },
    };
  }

  /** State chung của game dạng "lật thẻ tìm cặp". */
  function memoryState() {
    return {
      cards: [], up: [], matched: 0, mistakes: 0, pairsTotal: 0,
      pairIds: [], matchedIds: [],
      busy: false, finished: false, starText: '', newBadges: [],

      /** Nạp bộ thẻ từ json_script "round-data". */
      loadCards() {
        const data = readJson('round-data', {});
        this.cards = (data.cards || []).map(c => ({ ...c, done: false }));
        this.pairsTotal = (data.pairs || []).length;
        this.pairIds = (data.pairs || []).map(p => p.pair_id);
        if (!this.pairsTotal) this.finished = true;
      },

      isUp(i) {
        return this.up.includes(i);
      },

      /**
       * Xử lý khi đã lật đủ 2 thẻ: trùng pair_id là ghép đúng.
       * `wrongDelay` — thời gian úp lại khi sai (mỗi game chỉnh khác nhau chút).
       */
      resolvePair(submitUrl, wrongDelay) {
        this.busy = true;
        const [a, b] = this.up;
        if (this.cards[a].pair_id === this.cards[b].pair_id) {
          this.cards[a].done = true;
          this.cards[b].done = true;
          this.matched++;
          this.matchedIds.push(this.cards[a].pair_id);
          feedback(true);
          this.up = [];
          this.busy = false;
          if (this.matched === this.pairsTotal) this.submit(submitUrl);
        } else {
          this.mistakes++;
          feedback(false);
          setTimeout(() => { this.up = []; this.busy = false; }, wrongDelay || 800);
        }
      },

      /** Nộp ván ghép cặp (payload khác game trắc nghiệm). */
      submit(submitUrl) {
        return submitRound(submitUrl, {
          pairs_total: this.pairsTotal,
          pairs_matched: this.matched,
          mistakes: this.mistakes,
          matched_pair_ids: this.matchedIds,
          pair_ids: this.pairIds,
        }, this);
      },
    };
  }

  window.gameCommon = {
    getCookie: getCookie,
    readJson: readJson,
    playHintOnLoad: playHintOnLoad,
    starText: starText,
    feedback: feedback,
    wordAudioUrl: wordAudioUrl,
    playWordAudio: playWordAudio,
    playViName: playViName,
    submitRound: submitRound,
    quizState: quizState,
    memoryState: memoryState,
  };
})();
