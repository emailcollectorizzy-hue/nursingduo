# Phase 8: continuous multi-section scroll. Kills the section-done interstitial
# (mascot + progress code + buttons). Completing a section happens IN the flow:
# the finale chunk swaps to a compact celebration and the next section appends
# below — the user never stops scrolling.
import io

p = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
s = io.open(p, encoding="utf-8").read()

start = s.index("function setLessonStep(i) {")
end_marker = """  if (e.key === "ArrowLeft") {
    e.preventDefault();
    if (lessonIdx > 0) setLessonStep(lessonIdx - 1);
  }
});
"""
end = s.index(end_marker) + len(end_marker)
old = s[start:end]
assert "mountInlineRecall" in old and "finishSectionLesson" in old and "renderLessonStep" in old, "unexpected region"

new = r'''// ===== PULSE continuous-flow engine =====
// Sections render as stacked blocks inside one scroll (#ls-flow). Reaching a
// section's finale completes it IN PLACE (XP/streak/read state, compact inline
// celebration — no interstitial screen) and appends the next section below, so
// studying is one unbroken scroll. Recall gates stay inline (mountInlineRecall).
let _lsSteps = {};          // secIdx -> prepared steps (gates assigned)
let _lsCompletedFx = {};    // per-session guard so a finale only completes once
let _lsProgOffs = [];
let _lsSpy = null, _lsActiveRecall = null;

function lsPrepSteps(secIdx) {
  if (_lsSteps[secIdx]) return _lsSteps[secIdx];
  const sx = STUDY[secIdx];
  const steps = splitSectionIntoSteps(sx.html, sx.title);
  assignQuickChecks(steps, sx.title);
  assignFlashcardsPerSubsection(steps, sx.title);
  _lsSteps[secIdx] = steps;
  return steps;
}

// Earliest read-chunk whose flash-gate is unpassed — everything after it renders locked.
function lsLockFrom(secIdx) {
  const sx = STUDY[secIdx];
  const steps = _lsSteps[secIdx] || [];
  for (let i = 0; i < steps.length; i++) {
    const st = steps[i];
    if (st.kind !== "read") continue;
    if ((st.flashCards || []).length && !state.lessonGate[sx.id + ":" + i]) return i;
  }
  return steps.length;
}

function lsScrollToChunk(secIdx, i, smooth) {
  const el = document.getElementById("ls-chunk-" + secIdx + "-" + i);
  if (el) el.scrollIntoView({ behavior: (smooth && !PM.reduced) ? "smooth" : "auto", block: "start" });
}

function setLessonStep(i) {
  // a "step" is a stacked chunk; navigating = scrolling to it.
  // state.lessonStep keeps FURTHEST-step semantics (resume CTA / path % read it).
  const steps = _lsSteps[currentSectionIdx] || lessonSteps;
  lessonIdx = Math.max(0, Math.min(steps.length - 1, i));
  const sx = STUDY[currentSectionIdx];
  state.lessonStep = state.lessonStep || {};
  state.lessonStep[sx.id] = Math.max(state.lessonStep[sx.id] || 0, lessonIdx);
  saveState();
  lsScrollToChunk(currentSectionIdx, lessonIdx, true);
}

const _lsPad2 = n => String(n).padStart(2, "0");

function lsCompleteInnerHtml(secIdx, bonusXp, fresh) {
  const sx = STUDY[secIdx];
  const next = secIdx + 1 < STUDY.length;
  const disp = (typeof chDisp === "function" && IS_COURSE) ? chDisp(sx.title) : sx.title;
  return `<div class="ls-complete">
    <span class="eyebrow">SECTION ${_lsPad2(secIdx + 1)} COMPLETE${fresh && bonusXp ? " · +" + bonusXp + " XP" : ""}</span>
    <div class="ls-complete-row">🎉 ${escapeHtml(disp)}</div>
    <div class="ls-complete-stats"><span>🔥 <b class="num">${state.dayStreak.count}</b> day streak</span><span>📖 <b class="num">${state.read.length}/${STUDY.length}</b> sections</span></div>
    <div class="ls-next-hint eyebrow">${next ? "KEEP SCROLLING ↓" : "COURSE END — EVERY SECTION DONE 🏆"}</div>
  </div>`;
}

function lsFinaleHtml(secIdx, stepIdx, locked, isCheckpoint) {
  const sx = STUDY[secIdx];
  const done = state.read.includes(sx.id);
  const lockHtml = locked ? `<div class="ls-lock-overlay"><div class="ls-lock-card">🔒 <b>Locked</b><span>Pass the recall check above to keep going</span></div></div>` : "";
  let inner;
  if (done) {
    inner = lsCompleteInnerHtml(secIdx, 0, false);
  } else if (isCheckpoint) {
    const cpDone = !!(state._cpUiDone && state._cpUiDone[sx.id]);
    inner = `<div class="checkpoint-intro"><div class="big">🧠</div><h3>Section checkpoint</h3>
      <p>Lock it in with a few real exam questions — the next section rolls in right after.</p>
      <div class="ls-finale-btns">
        <button class="btn" data-cp="${secIdx}">${cpDone ? "↻ Retake checkpoint" : "🧠 Start checkpoint →"}</button>
        <button class="btn ghost" data-cpskip="${secIdx}">Skip for now ↓</button>
      </div></div>`;
  } else {
    inner = `<div class="checkpoint-intro"><div class="big">🏁</div><h3>End of section</h3>
      <p>Keep scrolling — the next section picks up right below.</p></div>`;
  }
  return `<section class="ls-chunk ls-cp ls-finale ${locked ? "ls-locked" : ""}" data-sec="${secIdx}" data-step="${stepIdx}" id="ls-chunk-${secIdx}-${stepIdx}">
    <div class="ls-chunk-head"><span class="eyebrow">FINALE</span></div>
    <div class="lesson-card cp-finale" id="ls-finbody-${secIdx}">${inner}</div>${lockHtml}</section>`;
}

function lsSectionHtml(secIdx) {
  const sx = STUDY[secIdx];
  const steps = lsPrepSteps(secIdx);
  const total = steps.length;
  const lockFrom = lsLockFrom(secIdx);
  const bookmarked = state.bookmarks.sections.includes(sx.id);
  const tRaw = sx.title || "";
  const sep = tRaw.indexOf(" · ");
  const chapLabel = sep > 0 ? tRaw.slice(0, sep) : "";
  const dispTitle = sep > 0 ? tRaw.slice(sep + 3) : tRaw;
  const readCount = steps.filter(st => st.kind === "read").length;
  const mins = Math.max(1, Math.round(steps.reduce((n, st) => n + ((st.html || "").length / 1200), 0)));
  const hero = `<div class="ls-hero"><div class="ls-hero-in">
      <div class="eyebrow ls-hero-eyebrow">${chapLabel ? escapeHtml(chapLabel.toUpperCase()) + " · " : ""}SECTION ${_lsPad2(secIdx + 1)} / ${_lsPad2(STUDY.length)}</div>
      <h1 class="ls-hero-title">${escapeHtml(dispTitle)}</h1>
      <div class="ls-hero-meta"><span class="eyebrow">${readCount} STEPS · ~${mins} MIN</span>
        <button class="bookmark-btn ${bookmarked ? "active" : ""}" data-bookmark="${escapeAttr(sx.id)}" title="Bookmark" aria-label="Bookmark">★</button></div>
      <div class="ls-scroll-hint" aria-hidden="true">↓</div>
    </div></div>`;
  let hasCp = false;
  const chunks = steps.map((st, i) => {
    const locked = i > lockFrom;
    if (st.kind === "checkpoint") { hasCp = true; return lsFinaleHtml(secIdx, i, locked, true); }
    const gateKey = sx.id + ":" + i;
    const fcs = st.flashCards || [];
    const passed = !!state.lessonGate[gateKey];
    const csCur = (state.chunkStatus || {})[gateKey] || "";
    const head = (st.title && st.title !== "Overview")
      ? `<div class="ls-chunk-head" data-num="${_lsPad2(i + 1)}"><span class="eyebrow">STEP ${_lsPad2(i + 1)} / ${_lsPad2(total)}</span><h3 class="ls-chunk-title">${escapeHtml(st.title)}</h3></div>`
      : `<div class="ls-chunk-head" data-num="${_lsPad2(i + 1)}"><span class="eyebrow">OVERVIEW</span></div>`;
    const gateDone = (fcs.length && passed) ? `<span class="ls-gate-done">✓ Recall passed</span>` : "";
    const recallHost = (fcs.length && !passed) ? `<div class="ls-recall" id="ls-recall-${secIdx}-${i}"></div>` : "";
    const lockHtml = locked ? `<div class="ls-lock-overlay"><div class="ls-lock-card">🔒 <b>Locked</b><span>Pass the recall check above to keep going</span></div></div>` : "";
    return `<section class="ls-chunk ${locked ? "ls-locked" : ""}" data-sec="${secIdx}" data-step="${i}" id="ls-chunk-${secIdx}-${i}">
      ${head}
      <div class="lesson-card ${st.title === "Overview" ? "overview" : ""}">${st.html}</div>
      <div class="ls-chunk-foot">
        <div class="chunk-status" data-key="${escapeAttr(gateKey)}" title="Flag this step as mastered or needs review">
          <button class="cs-btn cs-got ${csCur === "got" ? "active" : ""}" type="button" data-cs="got">✓ Got it</button>
          <button class="cs-btn cs-flag ${csCur === "flag" ? "active" : ""}" type="button" data-cs="flag">🔁 Review</button>
        </div>
        <div class="spacer"></div>${gateDone}
      </div>${recallHost}${lockHtml}</section>`;
  }).join("");
  const finale = hasCp ? "" : lsFinaleHtml(secIdx, total, lockFrom < total, false);
  return `<div class="ls-section" id="ls-sec-${secIdx}" data-sec="${secIdx}">${hero}<div class="ls-chunks">${chunks}${finale}</div></div>`;
}

function lsSyncRail(secIdx) {
  const dotsEl = document.getElementById("ls-rail-dots");
  if (!dotsEl) return;
  const sx = STUDY[secIdx];
  const steps = _lsSteps[secIdx] || [];
  const lockFrom = lsLockFrom(secIdx);
  dotsEl.innerHTML = steps.map((st, i) => {
    const gatePassed = st.kind === "read" && (!(st.flashCards || []).length || !!state.lessonGate[sx.id + ":" + i]);
    const cls = ["ls-dot"];
    if (i > lockFrom) cls.push("locked");
    if (st.kind === "checkpoint") cls.push("cp");
    else if (i <= lockFrom && gatePassed) cls.push("done");
    return `<button class="${cls.join(" ")}" data-sec="${secIdx}" data-step="${i}" title="${escapeAttr(st.title || ("Step " + (i + 1)))}" aria-label="Step ${i + 1}"></button>`;
  }).join("");
  dotsEl.querySelectorAll(".ls-dot").forEach(d => d.addEventListener("click", () => {
    const i = parseInt(d.dataset.step);
    if (i > lsLockFrom(secIdx)) { showToast("🔒 Pass the recall check first"); return; }
    lsScrollToChunk(secIdx, i, true);
  }));
}

function lsRebuildSpy() {
  try { if (_lsSpy) _lsSpy.disconnect(); } catch (e) {}
  const chunks = document.querySelectorAll("#ls-flow .ls-chunk");
  if (!chunks.length) return;
  _lsSpy = PM.spy(chunks, (node) => {
    const sec = parseInt(node.dataset.sec), stp = parseInt(node.dataset.step);
    if (isNaN(sec) || isNaN(stp)) return;
    if (sec !== currentSectionIdx) {
      currentSectionIdx = sec;
      state.lastSection = sec; saveState();
      lessonSteps = _lsSteps[sec] || lessonSteps;
      try { syncSecCascade(); } catch (e) {}
      const sc = document.getElementById("sec-counter"); if (sc) sc.textContent = `Section ${sec + 1} of ${STUDY.length}`;
      const pv = document.getElementById("sec-prev"); if (pv) pv.disabled = sec === 0;
      const nx = document.getElementById("sec-next"); if (nx) nx.disabled = sec === STUDY.length - 1 || !sectionUnlocked(sec + 1);
      lsSyncRail(sec);
    }
    const total = (_lsSteps[sec] || []).length;
    lessonIdx = Math.min(stp, Math.max(0, total - 1));
    const cnt = document.getElementById("ls-rail-count");
    if (cnt && total) cnt.textContent = _lsPad2(Math.min(stp + 1, total)) + "/" + _lsPad2(total);
    document.querySelectorAll("#ls-rail-dots .ls-dot").forEach(d =>
      d.classList.toggle("cur", parseInt(d.dataset.step) === stp && parseInt(d.dataset.sec) === sec));
    if (!node.classList.contains("ls-locked") && stp < total) {
      const sx = STUDY[sec];
      state.lessonStep = state.lessonStep || {};
      const prev = state.lessonStep[sx.id] || 0;
      if (stp > prev) { state.lessonStep[sx.id] = stp; saveState(); questProgress("STUDY_STEPS", 1); }
    }
  });
}

function lsWireSection(secIdx) {
  const block = document.getElementById("ls-sec-" + secIdx);
  if (!block) return;
  const sx = STUDY[secIdx];
  const steps = lsPrepSteps(secIdx);

  block.querySelectorAll("[data-bookmark]").forEach(btn => btn.addEventListener("click", e => {
    e.stopPropagation();
    const id = btn.dataset.bookmark;
    const i = state.bookmarks.sections.indexOf(id);
    if (i >= 0) state.bookmarks.sections.splice(i, 1); else state.bookmarks.sections.push(id);
    btn.classList.toggle("active"); saveState();
  }));

  block.querySelectorAll(".chunk-status .cs-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const wrap = btn.closest(".chunk-status");
      if (!wrap) return;
      const key = wrap.dataset.key;
      const target = btn.dataset.cs;
      state.chunkStatus = state.chunkStatus || {};
      if (state.chunkStatus[key] === target) delete state.chunkStatus[key];
      else state.chunkStatus[key] = target;
      saveState();
      wrap.querySelectorAll(".cs-btn").forEach(b => b.classList.toggle("active", state.chunkStatus[key] === b.dataset.cs));
    });
  });

  // scroll-reveal tags (PM.reveal honors reduced-motion)
  block.querySelectorAll(".ls-chunk .lesson-card").forEach(card => {
    card.querySelectorAll(":scope > p, :scope > ul, :scope > ol, :scope > h4, :scope > .callout").forEach(el => el.setAttribute("data-rv", ""));
    card.querySelectorAll(":scope > table").forEach(el => el.setAttribute("data-rv", "table"));
    card.querySelectorAll("img").forEach(el => el.setAttribute("data-rv", "scale"));
  });
  PM.reveal(block);

  // hero shrink — driven by this block's own traversal
  const hero = block.querySelector(".ls-hero");
  if (hero) {
    _lsProgOffs.push(PM.progress(block, (pp, r) => {
      const vh = window.innerHeight || 1;
      const hp = Math.max(0, Math.min(1, ((-r.top) + vh * 0.04) / (vh * 0.5)));
      hero.style.setProperty("--hp", hp.toFixed(3));
    }));
  }

  // checkpoint CTA + skip (checkpoint stays MCQ in the focus shell)
  const cpBtn = block.querySelector("[data-cp]");
  if (cpBtn) cpBtn.addEventListener("click", () => {
    const sQ = shuffleArray(QUIZ.filter(q => q.section === sx.title && q.type !== "sata").slice()).slice(0, 6);
    const cpData = sQ.map(q => ({ q: q.stem, opts: q.options, correctIdx: (q.correct && q.correct[0] != null) ? q.correct[0] : 0, rats: q.rationales || [], id: q.id }));
    if (!cpData.length) { lsCompleteSection(secIdx); return; }
    _cpWrong = 0; _cpTotal = cpData.length;
    runCheckpointInFocus(cpData, sx.id, () => {
      state._cpUiDone = state._cpUiDone || {}; state._cpUiDone[sx.id] = true; saveState();
      lsCompleteSection(secIdx);
    });
  });
  const cpSkip = block.querySelector("[data-cpskip]");
  if (cpSkip) cpSkip.addEventListener("click", () => { _cpTotal = 0; _cpWrong = 0; lsCompleteSection(secIdx); });

  // inline recall at the lock boundary
  const lockFrom = lsLockFrom(secIdx);
  if (lockFrom < steps.length) mountInlineRecall(secIdx, lockFrom);

  // finale watcher — completes the section in the flow when it scrolls into view
  const fin = block.querySelector(".ls-finale");
  if (fin && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(ens => { if (ens.some(en => en.isIntersecting)) lsCheckFinale(secIdx); }, { threshold: 0.3 });
    io.observe(fin);
    fin._lsIO = io;
  }

  markRefContext(block);
}

function lsCheckFinale(secIdx) {
  const sx = STUDY[secIdx];
  const steps = _lsSteps[secIdx];
  if (!steps) return;
  const fin = document.getElementById("ls-finbody-" + secIdx);
  if (!fin) return;
  const r = fin.getBoundingClientRect();
  if (r.top > (window.innerHeight || 0) || r.bottom < 0) return;     // not on screen
  if (lsLockFrom(secIdx) < steps.length) return;                     // recall gates remain
  const hasCp = steps.some(st => st.kind === "checkpoint");
  const cpDone = !!(state._cpUiDone && state._cpUiDone[sx.id]);
  if (hasCp && !cpDone && !state.read.includes(sx.id)) return;       // waiting on checkpoint CTA / skip
  lsCompleteSection(secIdx);
}

// Complete the section IN the flow — no interstitial: bank XP/read/streak, swap the
// finale to a compact celebration, append the next section below, keep scrolling.
function lsCompleteSection(secIdx) {
  const sx = STUDY[secIdx];
  const fin = document.getElementById("ls-finbody-" + secIdx);
  if (!_lsCompletedFx[secIdx]) {
    _lsCompletedFx[secIdx] = true;
    const finChunk = fin ? fin.closest(".ls-finale") : null;
    if (finChunk && finChunk._lsIO) { try { finChunk._lsIO.disconnect(); } catch (e) {} }
    const firstTime = !state.read.includes(sx.id);
    if (firstTime) {
      state.read.push(sx.id); state.lastSection = secIdx; saveState();
      const picker = document.getElementById("sec-jump");
      if (picker) {
        const opt = Array.from(picker.options).find(o => o.value === String(secIdx));
        if (opt) opt.text = "✓ " + (IS_COURSE ? chDisp(sx.title) : sx.title);
      }
      try { checkNewBadges(); } catch (e) {}
    }
    // perfect checkpoint → gild the section (legendary 👑)
    if (_cpTotal > 0 && _cpWrong === 0) {
      questProgress("PERFECT_CHECKPOINT", 1);
      if (!state.path.legendary) state.path.legendary = {};
      const wasLeg = !!state.path.legendary[sx.id];
      state.path.legendary[sx.id] = true; saveState();
      if (!wasLeg) {
        showToast("👑 Perfect checkpoint — section gilded!");
        if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
          const c = document.createElement("div");
          c.className = "crown-drop"; c.textContent = "👑";
          document.body.appendChild(c);
          void c.offsetWidth; c.classList.add("go");
          setTimeout(() => c.remove(), 1700);
        }
        setMascotEmoji("🎉", 1500);
      }
      creditXpOnce("perfcp:" + sx.id, 15);
    }
    _cpTotal = 0; _cpWrong = 0;
    const gotBonus = creditXpOnce("sec:" + sx.id, 20);
    if (gotBonus) { bumpGoal(1); touchDayStreak(); }
    if (fin) fin.innerHTML = lsCompleteInnerHtml(secIdx, gotBonus ? 20 : 0, firstTime || gotBonus);
    if (firstTime || gotBonus) {
      try { launchConfetti(); } catch (e) {}
      try { sfx.complete(); } catch (e) {}
    }
    const nx = document.getElementById("sec-next");
    if (nx && secIdx === currentSectionIdx && secIdx + 1 < STUDY.length) nx.disabled = !sectionUnlocked(secIdx + 1);
  }
  if (secIdx + 1 < STUDY.length) lsAppendSection(secIdx + 1);
}

// kept as a thin alias for any legacy callers
function finishSectionLesson() { lsCompleteSection(currentSectionIdx); }

function lsAppendSection(secIdx) {
  const flow = document.getElementById("ls-flow");
  if (!flow || document.getElementById("ls-sec-" + secIdx)) return;
  lsPrepSteps(secIdx);
  flow.insertAdjacentHTML("beforeend", lsSectionHtml(secIdx));
  lsWireSection(secIdx);
  lsPruneBlocks();
  lsRebuildSpy();
}

// Keep at most 3 section blocks in the DOM — drop blocks far above the viewport,
// compensating the scroll position so nothing visibly jumps.
function lsPruneBlocks() {
  const flow = document.getElementById("ls-flow");
  if (!flow) return;
  let blocks = Array.from(flow.children).filter(b => b.classList && b.classList.contains("ls-section"));
  while (blocks.length > 3) {
    const b = blocks[0];
    const r = b.getBoundingClientRect();
    if (r.bottom >= -300) break;
    const h = b.offsetHeight;
    b.remove();
    window.scrollBy({ top: -h, left: 0, behavior: "auto" });
    blocks = Array.from(flow.children).filter(x => x.classList && x.classList.contains("ls-section"));
  }
}

// Inline recall check — a flashcard moment embedded in the scroll. "Don't know"
// requeues to the end; the gate passes only when every card is rated above
// don't-know. Same SRS keys + lessonGate semantics as ever.
function mountInlineRecall(secIdx, stepIdx) {
  const sx = STUDY[secIdx];
  const steps = _lsSteps[secIdx] || [];
  const st = steps[stepIdx];
  if (!st || st.kind !== "read") return;
  const fcs = st.flashCards || [];
  const gateKey = sx.id + ":" + stepIdx;
  if (!fcs.length || state.lessonGate[gateKey]) return;
  const host = document.getElementById("ls-recall-" + secIdx + "-" + stepIdx);
  if (!host || host.dataset.mounted) return;
  host.dataset.mounted = "1";
  const queue = fcs.slice();
  const startSize = queue.length;
  let idx = 0, revealed = false;

  function renderOne() {
    const c = queue[idx];
    if (!c) { pass(); return; }
    revealed = false;
    const completed = Math.max(0, idx - (queue.length - startSize));
    const repeats = queue.length - startSize;
    host.innerHTML = `<div class="rc-card">
      <div class="rc-head">
        <span class="eyebrow">📇 RECALL CHECK · ${_lsPad2(Math.min(completed + 1, startSize))}/${_lsPad2(startSize)}${repeats > 0 ? " · +" + repeats : ""}</span>
        <span class="rc-dots">${Array.from({ length: startSize }, (_, k) => `<i class="${k < completed ? "on" : ""}"></i>`).join("")}</span>
      </div>
      <div class="rc-prompt">${flashPrompt(c)}</div>
      <button class="btn secondary rc-reveal" type="button">👁 Reveal answer <kbd class="conf-k">space</kbd></button>
      <div class="rc-answer" style="display:none;">
        <div class="rc-a-box">${flashAnswer(c)}</div>
        ${c.why ? `<div class="fc-gate-why"><strong>💡 Why it's right —</strong> ${renderWhy(c.why)}</div>` : ""}
        <div class="fc-gate-confs">
          <button class="conf-btn" data-c="3" type="button" title="J — nailed it instantly"><span class="cb-key">J</span><span class="cb-lbl">🎯 Knew it</span></button>
          <button class="conf-btn" data-c="2" type="button" title="K — got it but hesitated"><span class="cb-key">K</span><span class="cb-lbl">🤔 Shaky</span></button>
          <button class="conf-btn" data-c="1" type="button" title="L — guessed correctly"><span class="cb-key">L</span><span class="cb-lbl">🤷 Guess</span></button>
          <button class="conf-btn" data-c="0" type="button" title=";  or M — didn't know it"><span class="cb-key">;</span><span class="cb-lbl">😬 Don't know</span></button>
        </div>
      </div>
    </div>`;
    markRefContext(host);
    host.querySelector(".rc-reveal").addEventListener("click", reveal);
    host.querySelector(".rc-prompt").addEventListener("click", reveal);
    host.querySelectorAll(".conf-btn").forEach(b => b.addEventListener("click", () => grade(parseInt(b.dataset.c, 10))));
    _lsActiveRecall = { secIdx, stepIdx, reveal, grade, isRevealed: () => revealed };
  }

  function reveal() {
    if (revealed) return;
    revealed = true;
    const a = host.querySelector(".rc-answer");
    const rv = host.querySelector(".rc-reveal");
    if (rv) rv.style.display = "none";
    if (a) { a.style.display = ""; a.classList.add("fc-flip-in"); setTimeout(() => a.classList.remove("fc-flip-in"), 520); }
    try { haptic.reveal(); } catch (e) {}
  }

  function grade(conf) {
    if (!revealed) return;
    const c = queue[idx];
    const cardId = c.fid ? ("fc:" + c.fid) : ("f:" + (c.q || "").slice(0, 80));
    const outcome = conf === 3 ? "right-sure" : conf === 2 ? "right-shaky" : conf === 1 ? "right-guess" : "wrong";
    try { srsApply(cardId, "flashcard", outcome); } catch (e) {}
    try { touchDayStreak(); bumpGoal(1); } catch (e) {}
    const box = host.querySelector(".rc-a-box");
    if (outcome !== "wrong") {
      try { sfx.correct(); } catch (e) {} try { haptic.correct(); } catch (e) {}
      try { const r = host.getBoundingClientRect(); awardXp(5, r.left + 70, Math.max(80, r.top)); } catch (e) {}
      if (box) box.classList.add("fc-flash-good");
    } else {
      try { sfx.wrong(); } catch (e) {} try { haptic.wrong(); } catch (e) {}
      if (box) box.classList.add("fc-flash-bad");
      queue.push(c);
      try { showToast("🔁 You'll see that one again"); } catch (e) {}
    }
    idx++;
    setTimeout(renderOne, 360);
  }

  function pass() {
    state.lessonGate[gateKey] = 1;
    saveState();
    _lsActiveRecall = null;
    try { questProgress("STUDY_STEPS", 1); } catch (e) {}
    host.innerHTML = `<div class="ls-recall-done">✓ Recall passed — keep scrolling</div>`;
    lsGateComplete(secIdx, stepIdx);
  }

  renderOne();
}

// In-place unlock after an inline recall passes — no re-render, scroll stays put.
function lsGateComplete(secIdx, stepIdx) {
  const block = document.getElementById("ls-sec-" + secIdx);
  if (!block) return;
  const newLock = lsLockFrom(secIdx);
  block.querySelectorAll(".ls-chunk").forEach(ch => {
    const i = parseInt(ch.dataset.step);
    if (i <= newLock && ch.classList.contains("ls-locked")) {
      ch.classList.remove("ls-locked");
      ch.classList.add("ls-unlock");
      const ov = ch.querySelector(".ls-lock-overlay");
      if (ov) ov.remove();
    }
  });
  lsSyncRail(secIdx);
  const steps = _lsSteps[secIdx] || [];
  if (newLock < steps.length) mountInlineRecall(secIdx, newLock);
  PM.reveal(block);
  try { sfx.correct(); } catch (e) {}
  lsScrollToChunk(secIdx, stepIdx + 1, true);
  setTimeout(() => lsCheckFinale(secIdx), 700);
}

function renderLessonStep() {
  const area = document.getElementById("section-content");
  if (!area) return;
  try { if (_lsSpy) { _lsSpy.disconnect(); _lsSpy = null; } } catch (e) {}
  _lsProgOffs.forEach(off => { try { off(); } catch (e) {} });
  _lsProgOffs = [];
  _lsActiveRecall = null;
  _lsSteps = {};
  _lsSteps[currentSectionIdx] = lessonSteps;   // renderCurrentSection prepped these

  area.innerHTML = `<div class="ls-rail" id="ls-rail">
      <div class="ls-rail-track"><div class="ls-rail-fill" id="ls-rail-fill"></div></div>
      <div class="ls-rail-dots" id="ls-rail-dots"></div>
      <span class="ls-rail-count" id="ls-rail-count">${_lsPad2(Math.min(lessonIdx + 1, lessonSteps.length))}/${_lsPad2(lessonSteps.length)}</span>
    </div><div class="ls-flow" id="ls-flow">` + lsSectionHtml(currentSectionIdx) + `</div>`;
  lsWireSection(currentSectionIdx);
  lsSyncRail(currentSectionIdx);
  lsRebuildSpy();
  const flow = document.getElementById("ls-flow");
  const fill = document.getElementById("ls-rail-fill");
  if (flow && fill) _lsProgOffs.push(PM.progress(flow, pp => { fill.style.width = (pp * 100).toFixed(1) + "%"; }));

  // resume mid-section
  if (lessonIdx > 0) requestAnimationFrame(() => lsScrollToChunk(currentSectionIdx, Math.min(lessonIdx, lsLockFrom(currentSectionIdx)), false));
}

// Keyboard nav for the study lesson — Space reveals / J K L ; M grade the inline
// recall when it's on screen (ANY key flips mirror of the Cards tab); ArrowRight:
// next chunk (the recall blocks skipping); ArrowLeft: previous chunk.
function _lsRecallOnScreen() {
  if (!_lsActiveRecall) return false;
  const host = document.getElementById("ls-recall-" + _lsActiveRecall.secIdx + "-" + _lsActiveRecall.stepIdx);
  if (!host) return false;
  const r = host.getBoundingClientRect();
  return r.top < (window.innerHeight || 0) * 0.95 && r.bottom > 60;
}
document.addEventListener("keydown", e => {
  if (!document.getElementById("tab-study").classList.contains("active")) return;
  if (document.body.classList.contains("in-lesson")) return;   // focus shell owns the keys
  if (["INPUT","SELECT","TEXTAREA","BUTTON"].includes(document.activeElement.tagName)) return;
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if (_lsRecallOnScreen()) {
    if (!_lsActiveRecall.isRevealed() && (k === " " || k === "enter")) { e.preventDefault(); _lsActiveRecall.reveal(); return; }
    const map = { "j": 3, "k": 2, "l": 1, ";": 0, "m": 0 };
    if (_lsActiveRecall.isRevealed() && map.hasOwnProperty(k)) { e.preventDefault(); _lsActiveRecall.grade(map[k]); return; }
  }
  if (e.key === "ArrowRight") {
    e.preventDefault();
    const lockFrom = lsLockFrom(currentSectionIdx);
    const total = (_lsSteps[currentSectionIdx] || []).length;
    if (lessonIdx >= total - 1) {
      const nextBlock = document.getElementById("ls-sec-" + (currentSectionIdx + 1));
      if (nextBlock) nextBlock.scrollIntoView({ behavior: PM.reduced ? "auto" : "smooth", block: "start" });
      else lsScrollToChunk(currentSectionIdx, total, true);   // synthetic finale
      return;
    }
    if (lessonIdx + 1 > lockFrom) {
      const host = document.getElementById("ls-recall-" + currentSectionIdx + "-" + lockFrom);
      if (host) {
        showToast("✋ Recall check to continue");
        host.scrollIntoView({ behavior: PM.reduced ? "auto" : "smooth", block: "center" });
        const card = host.querySelector(".rc-card");
        if (card) { card.classList.remove("fc-nudge"); void card.offsetWidth; card.classList.add("fc-nudge"); }
      }
      return;
    }
    setLessonStep(lessonIdx + 1);
  }
  if (e.key === "ArrowLeft") {
    e.preventDefault();
    if (lessonIdx > 0) setLessonStep(lessonIdx - 1);
  }
});
'''

s = s[:start] + new + s[end:]

# ---- CSS: section blocks + inline completion celebration ----
anchor = ".ls-recall-done{ display:flex; align-items:center; gap:8px; color:var(--success); font-weight:700; font-size:14px; padding:14px 4px; }\n"
assert anchor in s
extra_css = """.ls-section{ position:relative; }
.ls-section + .ls-section{ margin-top:4vh; border-top:1px solid var(--border); }
.ls-finale .lesson-card{ text-align:center; }
.ls-finale-btns{ display:flex; gap:10px; justify-content:center; flex-wrap:wrap; margin-top:14px; }
.ls-complete{ display:flex; flex-direction:column; align-items:center; gap:10px; padding:18px 6px; }
.ls-complete-row{ font-family:var(--font-display); font-size:22px; font-weight:700; letter-spacing:-.01em; }
.ls-complete-stats{ display:flex; gap:22px; color:var(--text-dim); font-size:14px; }
.ls-complete-stats .num{ color:var(--text); }
.ls-next-hint{ margin-top:10px; color:var(--accent-1); animation:lsHint 1.8s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce){ .ls-next-hint{ animation:none; } }
"""
s = s.replace(anchor, anchor + extra_css)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("phase8 applied; replaced", len(old), "chars with", len(new))
