# Phase 7: inline recall checks in the scroll + cloze fix + editorial restyle.
# - Cloze cards rendered blank in the focus gate + stats preview (used c.q instead of
#   flashPrompt/flashAnswer) — fixed.
# - Sections whose chunks are all titled "Overview" got zero gates — fallback added.
# - Study scroll: recall checks are now INLINE flashcard cards embedded between chunks;
#   grading happens in the flow and unlocks the next chunks IN PLACE (no popup, no
#   re-render) — one continuous scroll until the section is done.
# - Drastic editorial restyle: chunk content flows directly on the canvas (no card box),
#   huge ghost Doto step numerals, accent rules, bigger reading type.
import io

p = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
s = io.open(p, encoding="utf-8").read()

def rep(old, new, what):
    global s
    assert old in s, "MISSING: " + what
    assert s.count(old) == 1, "AMBIGUOUS: " + what
    s = s.replace(old, new)

# ---- 1. cloze fix: focus gate ----
rep("""    const tag = escapeHtml(c.section || "Flashcard");
    const qHtml = c.qHtml || escapeHtml(c.q || "");
    const aHtml = c.aHtml || escapeHtml(c.a || "");""",
    """    const tag = escapeHtml(c.section || "Flashcard");
    const qHtml = flashPrompt(c);   // handles cloze (c.text) — c.q is empty for cloze cards
    const aHtml = flashAnswer(c);""", "gate cloze fix")

# ---- 2. cloze fix: stats preview ----
rep("""      const aHtml = card.aHtml || escapeHtml(card.a || "");
      const why = card.why ? `<div class="fc-gate-why"><strong>💡 Why it's right —</strong> ${renderWhy(card.why)}</div>` : "";
      const qHtml = card.qHtml || escapeHtml(card.q || "");""",
    """      const aHtml = flashAnswer(card);   // handles cloze (card.text)
      const why = card.why ? `<div class="fc-gate-why"><strong>💡 Why it's right —</strong> ${renderWhy(card.why)}</div>` : "";
      const qHtml = flashPrompt(card);""", "stats preview cloze fix")

# ---- 3. Overview-only sections: fall back to all read steps ----
rep("""function assignQuickChecks(steps, sectionTitle) {
  const reads = steps.filter(st => st.kind === "read" && st.title && st.title !== "Overview");
  if (!reads.length) return;""",
    """function assignQuickChecks(steps, sectionTitle) {
  let reads = steps.filter(st => st.kind === "read" && st.title && st.title !== "Overview");
  if (!reads.length) reads = steps.filter(st => st.kind === "read");   // section whose chunks are all "Overview"
  if (!reads.length) return;""", "qc overview fallback")
rep("""function assignFlashcardsPerSubsection(steps, sectionTitle) {
  const reads = steps.filter(st => st.kind === "read" && st.title && st.title !== "Overview");
  if (!reads.length) return;""",
    """function assignFlashcardsPerSubsection(steps, sectionTitle) {
  let reads = steps.filter(st => st.kind === "read" && st.title && st.title !== "Overview");
  if (!reads.length) reads = steps.filter(st => st.kind === "read");   // section whose chunks are all "Overview"
  if (!reads.length) return;""", "fc overview fallback")

# ---- 4. chunk markup: data-num ghost numerals + inline recall host (no gate button) ----
rep("""    const gate = fcs.length
      ? (passed
        ? `<span class="ls-gate-done">✓ Recall passed</span>`
        : `<button class="btn ls-gate-btn" data-step="${i}">📇 Recall check (${fcs.length}) →</button>`)
      : "";
    return `<section class="ls-chunk ${locked ? "ls-locked" : ""}${unlockCls}" data-step="${i}" id="ls-chunk-${i}">
      ${head}
      <div class="lesson-card ${st.title === "Overview" ? "overview" : ""}">${st.html}</div>
      <div class="ls-chunk-foot">
        <div class="chunk-status" data-key="${escapeAttr(gateKey)}" title="Flag this step as mastered or needs review">
          <button class="cs-btn cs-got ${csCur === "got" ? "active" : ""}" type="button" data-cs="got">✓ Got it</button>
          <button class="cs-btn cs-flag ${csCur === "flag" ? "active" : ""}" type="button" data-cs="flag">🔁 Review</button>
        </div>
        <div class="spacer"></div>${gate}
      </div>${lockHtml}</section>`;""",
    """    const gateDone = (fcs.length && passed) ? `<span class="ls-gate-done">✓ Recall passed</span>` : "";
    const recallHost = (fcs.length && !passed) ? `<div class="ls-recall" id="ls-recall-${i}" data-step="${i}"></div>` : "";
    return `<section class="ls-chunk ${locked ? "ls-locked" : ""}${unlockCls}" data-step="${i}" id="ls-chunk-${i}">
      ${head}
      <div class="lesson-card ${st.title === "Overview" ? "overview" : ""}">${st.html}</div>
      <div class="ls-chunk-foot">
        <div class="chunk-status" data-key="${escapeAttr(gateKey)}" title="Flag this step as mastered or needs review">
          <button class="cs-btn cs-got ${csCur === "got" ? "active" : ""}" type="button" data-cs="got">✓ Got it</button>
          <button class="cs-btn cs-flag ${csCur === "flag" ? "active" : ""}" type="button" data-cs="flag">🔁 Review</button>
        </div>
        <div class="spacer"></div>${gateDone}
      </div>${recallHost}${lockHtml}</section>`;""", "chunk markup recall host")

rep("""    const head = (st.title && st.title !== "Overview")
      ? `<div class="ls-chunk-head"><span class="eyebrow">STEP ${pad2(i + 1)} / ${pad2(total)}</span><h3 class="ls-chunk-title">${escapeHtml(st.title)}</h3></div>`
      : `<div class="ls-chunk-head"><span class="eyebrow">OVERVIEW</span></div>`;""",
    """    const head = (st.title && st.title !== "Overview")
      ? `<div class="ls-chunk-head" data-num="${pad2(i + 1)}"><span class="eyebrow">STEP ${pad2(i + 1)} / ${pad2(total)}</span><h3 class="ls-chunk-title">${escapeHtml(st.title)}</h3></div>`
      : `<div class="ls-chunk-head" data-num="${pad2(i + 1)}"><span class="eyebrow">OVERVIEW</span></div>`;""", "chunk head data-num")

# ---- 5. replace the gate-button wiring with inline-recall mounting ----
rep("""  // recall gates → existing focus-shell flash-gate flow; on pass, unlock + continue
  area.querySelectorAll(".ls-gate-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const i = parseInt(btn.dataset.step);
      const st = lessonSteps[i];
      runFlashGateInFocus(st.flashCards || [], s.id + ":" + i, () => {
        questProgress("STUDY_STEPS", 1);
        window._lsUnlocked = Math.min(i + 1, total - 1);
        window._lsScrollTo = Math.min(i + 1, total - 1);
        renderLessonStep();
      });
    });
  });""",
    """  // recall checks live INLINE in the scroll — mount the active one (at the lock boundary)
  _lsActiveRecall = null;
  if (lockFrom < total) mountInlineRecall(lockFrom);""", "inline recall mounting")

# ---- 6. new module functions: mountInlineRecall + lsGateComplete (before renderLessonStep) ----
rep("""let _lsSpy = null, _lsProgOff = null, _lsCpData = null;

function renderLessonStep() {""",
    """let _lsSpy = null, _lsProgOff = null, _lsCpData = null, _lsActiveRecall = null;

// Inline recall check — a flashcard moment embedded in the scroll. Same queue
// semantics as the old focus-shell gate ("don't know" requeues to the end; the
// gate passes only when every card is rated above don't-know), same SRS keys.
function mountInlineRecall(stepIdx) {
  const s = STUDY[currentSectionIdx];
  const st = lessonSteps[stepIdx];
  if (!st || st.kind !== "read") return;
  const fcs = st.flashCards || [];
  const gateKey = s.id + ":" + stepIdx;
  if (!fcs.length || state.lessonGate[gateKey]) return;
  const host = document.getElementById("ls-recall-" + stepIdx);
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
        <span class="eyebrow">📇 RECALL CHECK · ${String(Math.min(completed + 1, startSize)).padStart(2, "0")}/${String(startSize).padStart(2, "0")}${repeats > 0 ? " · +" + repeats : ""}</span>
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
    _lsActiveRecall = { stepIdx, reveal, grade, isRevealed: () => revealed };
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
    lsGateComplete(stepIdx);
  }

  renderOne();
}

// In-place unlock after an inline recall passes: unblur the now-reachable chunks,
// refresh the rail, mount the next recall, glide on. No re-render — the scroll
// position and reveal states stay exactly where the user left them.
function lsGateComplete(stepIdx) {
  const s = STUDY[currentSectionIdx];
  const area = document.getElementById("section-content");
  if (!area) return;
  const newLock = lsLockFrom(s);
  area.querySelectorAll(".ls-chunk").forEach(ch => {
    const i = parseInt(ch.dataset.step);
    if (i <= newLock && ch.classList.contains("ls-locked")) {
      ch.classList.remove("ls-locked");
      ch.classList.add("ls-unlock");
      const ov = ch.querySelector(".ls-lock-overlay");
      if (ov) ov.remove();
    }
  });
  area.querySelectorAll(".ls-dot").forEach(d => {
    const i = parseInt(d.dataset.step);
    d.classList.toggle("locked", i > newLock);
    const st = lessonSteps[i];
    if (st && st.kind === "read" && i < newLock) d.classList.add("done");
  });
  if (newLock < lessonSteps.length) mountInlineRecall(newLock);
  PM.reveal(area);
  try { sfx.correct(); } catch (e) {}
  lsScrollToChunk(stepIdx + 1, true);
}

function renderLessonStep() {""", "module fns")

# ---- 7. keyboard: recall keys + arrow nudge to the active recall ----
rep("""// Keyboard nav for the study lesson — ArrowRight: next chunk (a blocking gate fires
// instead of skipping); ArrowLeft: previous chunk.
document.addEventListener("keydown", e => {
  if (!document.getElementById("tab-study").classList.contains("active")) return;
  if (["INPUT","SELECT","TEXTAREA","BUTTON"].includes(document.activeElement.tagName)) return;
  if (e.key === "ArrowRight") {
    e.preventDefault();
    const s = STUDY[currentSectionIdx];
    const lockFrom = lsLockFrom(s);
    if (lessonIdx >= lessonSteps.length - 1) { document.getElementById("lsn-finish")?.click(); return; }
    if (lessonIdx + 1 > lockFrom) {
      const gbtn = document.querySelector(`.ls-gate-btn[data-step="${lockFrom}"]`);
      if (gbtn) { showToast("✋ Recall check to continue"); gbtn.click(); }
      return;
    }
    setLessonStep(lessonIdx + 1);
  }
  if (e.key === "ArrowLeft") {
    e.preventDefault();
    if (lessonIdx > 0) setLessonStep(lessonIdx - 1);
  }
});""",
    """// Keyboard nav for the study lesson — Space reveals / J K L ; M grade the inline
// recall when it's on screen; ArrowRight: next chunk (the recall blocks skipping);
// ArrowLeft: previous chunk.
function _lsRecallOnScreen() {
  if (!_lsActiveRecall) return false;
  const host = document.getElementById("ls-recall-" + _lsActiveRecall.stepIdx);
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
  // inline recall: ANY key flips, J/K/L/;/M grade — mirrors the Cards tab
  if (_lsRecallOnScreen()) {
    if (!_lsActiveRecall.isRevealed() && (k === " " || k === "enter")) { e.preventDefault(); _lsActiveRecall.reveal(); return; }
    const map = { "j": 3, "k": 2, "l": 1, ";": 0, "m": 0 };
    if (_lsActiveRecall.isRevealed() && map.hasOwnProperty(k)) { e.preventDefault(); _lsActiveRecall.grade(map[k]); return; }
  }
  if (e.key === "ArrowRight") {
    e.preventDefault();
    const s = STUDY[currentSectionIdx];
    const lockFrom = lsLockFrom(s);
    if (lessonIdx >= lessonSteps.length - 1) { document.getElementById("lsn-finish")?.click(); return; }
    if (lessonIdx + 1 > lockFrom) {
      const host = document.getElementById("ls-recall-" + lockFrom);
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
});""", "keyboard recall")

# ---- 8. CSS: editorial scroll + recall card ----
anchor = "@media (max-width:560px){ .ls-hero{ min-height:34vh; } .ls-chunks{ gap:26px; } }\n"
assert anchor in s
editorial_css = """
/* ===== Editorial scroll (PULSE v2) — content flows on the canvas, no card boxes ===== */
.ls-chunks{ gap:11vh; }
.ls-chunk:not(.ls-cp) > .lesson-card{ background:transparent; border:0; box-shadow:none; padding:0; min-height:0; font-size:16.5px; line-height:1.78; }
.ls-chunk:not(.ls-cp) > .lesson-card p{ margin:15px 0; }
.ls-chunk:not(.ls-cp) > .lesson-card li{ margin:8px 0; }
.ls-chunk:not(.ls-cp) > .lesson-card.overview{ border-left:0; }
.ls-chunk-head{ position:relative; margin:0 0 20px; padding-top:8px; z-index:0; }
.ls-chunk-head::before{ content:attr(data-num); position:absolute; top:-44px; right:-8px; font-family:var(--font-dot); font-weight:700; font-size:clamp(72px,13vw,136px); line-height:1; color:color-mix(in srgb, var(--text) 7%, transparent); pointer-events:none; z-index:-1; user-select:none; }
.ls-chunk-title{ font-size:var(--t-h1); line-height:1.1; }
.ls-chunk-head::after{ content:""; display:block; width:46px; height:3px; margin-top:14px; background:var(--accent-1); border-radius:2px; box-shadow:0 0 10px var(--accent-glow); }

/* inline recall check — the standout "moment" in the flow */
.ls-recall{ margin-top:26px; }
.rc-card{ position:relative; background:var(--surface); border:1px solid var(--accent-line); border-radius:var(--radius-lg); padding:24px 28px; box-shadow:var(--shadow), 0 0 44px -16px var(--accent-glow); overflow:hidden; }
.rc-card::before{ content:""; position:absolute; left:0; top:16px; bottom:16px; width:3px; background:var(--accent-1); border-radius:0 2px 2px 0; box-shadow:0 0 12px var(--accent-glow); }
.rc-head{ display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:14px; flex-wrap:wrap; }
.rc-dots{ display:flex; gap:4px; }
.rc-dots i{ width:7px; height:7px; border-radius:50%; background:var(--surface-3); }
.rc-dots i.on{ background:var(--success); box-shadow:0 0 6px color-mix(in srgb, var(--success) 60%, transparent); }
.rc-prompt{ font-size:20px; font-weight:700; line-height:1.5; margin-bottom:16px; font-family:var(--font-display); cursor:pointer; }
.rc-answer .rc-a-box{ background:color-mix(in srgb, var(--accent-1) 8%, var(--surface)); border:1px solid var(--accent-line); border-radius:12px; padding:14px 18px; font-size:17px; line-height:1.55; margin-bottom:12px; }
.rc-answer .fc-gate-confs{ padding:14px 0 0; justify-content:flex-start; }
.ls-recall-done{ display:flex; align-items:center; gap:8px; color:var(--success); font-weight:700; font-size:14px; padding:14px 4px; }
@media (max-width:560px){ .rc-card{ padding:18px 16px; } .rc-prompt{ font-size:17px; } .ls-chunk-head::before{ font-size:64px; top:-30px; } .ls-chunks{ gap:8vh; } }
"""
s = s.replace(anchor, anchor + editorial_css)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("phase7 applied")
