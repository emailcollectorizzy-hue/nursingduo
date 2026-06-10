# Phase 2: replace the stepped lesson pager with PULSE scrollytelling.
import io

p = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
s = io.open(p, encoding="utf-8").read()

# ---- 1. JS: replace setLessonStep .. keyboard-nav block ----
start = s.index("function setLessonStep(i) {")
end_marker = """  if (e.key === "ArrowLeft") {
    e.preventDefault();
    const bk = document.getElementById("lsn-back");
    if (bk && !bk.disabled) bk.click();
  }
});
"""
end = s.index(end_marker) + len(end_marker)
old = s[start:end]
assert "renderLessonStep" in old and "fulltext-toggle" in old, "unexpected JS block"

new_js = r'''function setLessonStep(i) {
  // PULSE scrollytelling: a "step" is a stacked chunk; navigating = scrolling to it.
  // state.lessonStep keeps FURTHEST-step semantics (resume CTA / path % read it).
  lessonIdx = Math.max(0, Math.min(lessonSteps.length - 1, i));
  const s = STUDY[currentSectionIdx];
  state.lessonStep = state.lessonStep || {};
  state.lessonStep[s.id] = Math.max(state.lessonStep[s.id] || 0, lessonIdx);
  saveState();
  lsScrollToChunk(lessonIdx, true);
}

function lsScrollToChunk(i, smooth) {
  const el = document.getElementById("ls-chunk-" + i);
  if (el) el.scrollIntoView({ behavior: (smooth && !PM.reduced) ? "smooth" : "auto", block: "start" });
}

// Earliest read-chunk whose flash-gate is unpassed — everything after it renders locked.
function lsLockFrom(s) {
  for (let i = 0; i < lessonSteps.length; i++) {
    const st = lessonSteps[i];
    if (st.kind !== "read") continue;
    const fcs = st.flashCards || [];
    if (fcs.length && !state.lessonGate[s.id + ":" + i]) return i;
  }
  return lessonSteps.length;
}

let _lsSpy = null, _lsProgOff = null, _lsCpData = null;

function renderLessonStep() {
  const s = STUDY[currentSectionIdx];
  const area = document.getElementById("section-content");
  const total = lessonSteps.length;
  const bookmarked = state.bookmarks.sections.includes(s.id);
  const pad2 = n => String(n).padStart(2, "0");
  const lockFrom = lsLockFrom(s);

  // teardown observers from the previous render
  try { if (_lsSpy) { _lsSpy.disconnect(); _lsSpy = null; } } catch (e) {}
  try { if (_lsProgOff) { _lsProgOff(); _lsProgOff = null; } } catch (e) {}

  // ---- pinned hero (content scrolls over it; shrinks/fades via --hp) ----
  const tRaw = s.title || "";
  const sep = tRaw.indexOf(" · ");
  const chapLabel = sep > 0 ? tRaw.slice(0, sep) : "";
  const dispTitle = sep > 0 ? tRaw.slice(sep + 3) : tRaw;
  const readCount = lessonSteps.filter(st => st.kind === "read").length;
  const mins = Math.max(1, Math.round(lessonSteps.reduce((n, st) => n + ((st.html || "").length / 1200), 0)));
  const heroHtml = `<div class="ls-hero" id="ls-hero"><div class="ls-hero-in">
      <div class="eyebrow ls-hero-eyebrow">${chapLabel ? escapeHtml(chapLabel.toUpperCase()) + " · " : ""}SECTION ${pad2(currentSectionIdx + 1)} / ${pad2(STUDY.length)}</div>
      <h1 class="ls-hero-title">${escapeHtml(dispTitle)}</h1>
      <div class="ls-hero-meta"><span class="eyebrow">${readCount} STEPS · ~${mins} MIN</span>
        <button class="bookmark-btn ${bookmarked ? "active" : ""}" id="bookmark-btn" title="Bookmark" aria-label="Bookmark">★</button></div>
      <div class="ls-scroll-hint" aria-hidden="true">↓</div>
    </div></div>`;

  // ---- sticky progress rail ----
  const dots = lessonSteps.map((st, i) => {
    const gatePassed = st.kind === "read" && (!(st.flashCards || []).length || !!state.lessonGate[s.id + ":" + i]);
    const cls = ["ls-dot"];
    if (i > lockFrom) cls.push("locked");
    if (st.kind === "checkpoint") cls.push("cp");
    else if (i <= lockFrom && gatePassed) cls.push("done");
    return `<button class="${cls.join(" ")}" data-step="${i}" title="${escapeAttr(st.title || ("Step " + (i + 1)))}" aria-label="Step ${i + 1}"></button>`;
  }).join("");
  const railHtml = `<div class="ls-rail" id="ls-rail">
      <div class="ls-rail-track"><div class="ls-rail-fill" id="ls-rail-fill"></div></div>
      <div class="ls-rail-dots">${dots}</div>
      <span class="ls-rail-count" id="ls-rail-count">${pad2(Math.min(lessonIdx + 1, total))}/${pad2(total)}</span>
    </div>`;

  // ---- chunks ----
  _lsCpData = null;
  const justUnlocked = (typeof window._lsUnlocked === "number") ? window._lsUnlocked : -1;
  window._lsUnlocked = undefined;
  const chunksHtml = lessonSteps.map((st, i) => {
    const locked = i > lockFrom;
    const unlockCls = (i === justUnlocked && !locked) ? " ls-unlock" : "";
    const lockHtml = locked ? `<div class="ls-lock-overlay"><div class="ls-lock-card">🔒 <b>Locked</b><span>Pass the recall check above to keep going</span></div></div>` : "";
    if (st.kind === "checkpoint") {
      const sQ = shuffleArray(QUIZ.filter(q => q.section === s.title && q.type !== "sata").slice()).slice(0, 6);
      _lsCpData = sQ.map(q => ({ q: q.stem, opts: q.options, correctIdx: (q.correct && q.correct[0] != null) ? q.correct[0] : 0, rats: q.rationales || [], id: q.id }));
      _cpWrong = 0; _cpTotal = _lsCpData.length;
      const cpDone = !!state._cpUiDone && state._cpUiDone[s.id];
      return `<section class="ls-chunk ls-cp ${locked ? "ls-locked" : ""}${unlockCls}" data-step="${i}" id="ls-chunk-${i}">
        <div class="ls-chunk-head"><span class="eyebrow">FINALE</span></div>
        <div class="lesson-card cp-finale">
          <div class="checkpoint-intro"><div class="big">🧠</div><h3>Section checkpoint</h3>
            <p>${_lsCpData.length ? "Answer " + _lsCpData.length + " items to lock in the section." : "Nice work — finish to complete this section."}</p>
            ${_lsCpData.length ? `<button class="btn" id="lsn-cp-cta" style="display:block;margin:14px auto 0;">${cpDone ? "↻ Retake checkpoint" : "🧠 Start checkpoint (" + _lsCpData.length + ") →"}</button>` : ""}
          </div>
          <div class="ls-chunk-foot" style="justify-content:center;"><button class="btn cta-green" id="lsn-finish">Finish section ✓</button></div>
        </div>${lockHtml}</section>`;
    }
    const gateKey = s.id + ":" + i;
    const fcs = st.flashCards || [];
    const passed = !!state.lessonGate[gateKey];
    const csCur = (state.chunkStatus || {})[gateKey] || "";
    const head = (st.title && st.title !== "Overview")
      ? `<div class="ls-chunk-head"><span class="eyebrow">STEP ${pad2(i + 1)} / ${pad2(total)}</span><h3 class="ls-chunk-title">${escapeHtml(st.title)}</h3></div>`
      : `<div class="ls-chunk-head"><span class="eyebrow">OVERVIEW</span></div>`;
    const gate = fcs.length
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
      </div>${lockHtml}</section>`;
  }).join("");

  area.innerHTML = heroHtml + railHtml + `<div class="ls-chunks" id="ls-chunks">${chunksHtml}</div>`;

  // ---- wiring ----
  document.getElementById("bookmark-btn")?.addEventListener("click", e => {
    e.stopPropagation();
    const i = state.bookmarks.sections.indexOf(s.id);
    if (i >= 0) state.bookmarks.sections.splice(i, 1); else state.bookmarks.sections.push(s.id);
    e.target.classList.toggle("active"); saveState();
  });

  // per-chunk mastery chips
  area.querySelectorAll(".chunk-status .cs-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const wrap = btn.closest(".chunk-status");
      if (!wrap) return;
      const key = wrap.dataset.key;
      const target = btn.dataset.cs;
      state.chunkStatus = state.chunkStatus || {};
      const cur = state.chunkStatus[key];
      if (cur === target) delete state.chunkStatus[key];
      else state.chunkStatus[key] = target;
      saveState();
      wrap.querySelectorAll(".cs-btn").forEach(b => b.classList.toggle("active", state.chunkStatus[key] === b.dataset.cs));
    });
  });

  // recall gates → existing focus-shell flash-gate flow; on pass, unlock + continue
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
  });

  // checkpoint runs in the focus shell, one item at a time (unchanged flow)
  const cpCta = document.getElementById("lsn-cp-cta");
  if (cpCta) cpCta.addEventListener("click", () => {
    runCheckpointInFocus(_lsCpData, s.id, () => {
      state._cpUiDone = state._cpUiDone || {}; state._cpUiDone[s.id] = true; saveState();
      window._lsScrollTo = total - 1;
      renderLessonStep();
    });
  });
  document.getElementById("lsn-finish")?.addEventListener("click", finishSectionLesson);

  // rail dots → scroll-nav (locked dots blocked)
  area.querySelectorAll(".ls-dot").forEach(d => d.addEventListener("click", () => {
    const i = parseInt(d.dataset.step);
    if (i > lockFrom) { showToast("🔒 Pass the recall check first"); return; }
    setLessonStep(i);
  }));

  // scroll-reveal tags inside each chunk (PM.reveal honors reduced-motion)
  area.querySelectorAll(".ls-chunk .lesson-card").forEach(card => {
    card.querySelectorAll(":scope > p, :scope > ul, :scope > ol, :scope > h4, :scope > .callout").forEach(el => el.setAttribute("data-rv", ""));
    card.querySelectorAll(":scope > table").forEach(el => el.setAttribute("data-rv", "table"));
    card.querySelectorAll("img").forEach(el => el.setAttribute("data-rv", "scale"));
  });
  PM.reveal(area);

  // rail fill + hero shrink, one rAF-throttled scroll listener
  const hero = document.getElementById("ls-hero");
  const chunksEl = document.getElementById("ls-chunks");
  const fill = document.getElementById("ls-rail-fill");
  const cnt = document.getElementById("ls-rail-count");
  if (chunksEl && fill) {
    _lsProgOff = PM.progress(chunksEl, (p) => {
      fill.style.width = (p * 100).toFixed(1) + "%";
      if (hero) {
        const vh = window.innerHeight || 1;
        const hp = Math.max(0, Math.min(1, (window.scrollY || 0) / (vh * 0.5)));
        hero.style.setProperty("--hp", hp.toFixed(3));
      }
    });
  }

  // scroll-spy: active dot + furthest-read tracking
  const chunkNodes = area.querySelectorAll(".ls-chunk");
  _lsSpy = PM.spy(chunkNodes, (node, i) => {
    if (i < 0) return;
    lessonIdx = i;
    if (cnt) cnt.textContent = pad2(i + 1) + "/" + pad2(total);
    area.querySelectorAll(".ls-dot").forEach((d, j) => d.classList.toggle("cur", j === i));
    if (!node.classList.contains("ls-locked")) {
      state.lessonStep = state.lessonStep || {};
      const prev = state.lessonStep[s.id] || 0;
      if (i > prev) { state.lessonStep[s.id] = i; saveState(); questProgress("STUDY_STEPS", 1); }
    }
  });

  markRefContext(area);

  // resume / continue position
  const tgt = (typeof window._lsScrollTo === "number") ? window._lsScrollTo : (lessonIdx > 0 ? lessonIdx : -1);
  window._lsScrollTo = undefined;
  if (tgt > 0) requestAnimationFrame(() => lsScrollToChunk(Math.min(tgt, lockFrom), false));
}
'''

new_js += r'''
// Keyboard nav for the study lesson — ArrowRight: next chunk (a blocking gate fires
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
});
'''
# unescape the \u escapes we used for readability in this python source
new_js = new_js.encode().decode("unicode_escape").encode("latin-1", "backslashreplace").decode("utf-8") if False else new_js

s = s[:start] + new_js + s[end:]

# ---- 2. remove fullTextOpen remnants ----
s = s.replace("let fullTextOpen = false;\n", "")
s = s.replace("  fullTextOpen = false;\n", "")

# ---- 3. CSS: retarget #lsn-next.btn-gate to .ls-gate-btn ----
s = s.replace("#lsn-next.btn-gate {", ".ls-gate-btn.btn-gate, .ls-gate-btn {")
s = s.replace("#lsn-next.btn-gate::before {", ".ls-gate-btn::before {")

# ---- 4. CSS: append scrollytelling styles to the PULSE component skin ----
anchor = "input:focus,select:focus{ border-color:var(--accent-1) !important; outline:none; box-shadow:0 0 0 3px var(--accent-glow); }\n"
assert anchor in s
scrolly_css = """
/* ===== Study scrollytelling (PULSE) ===== */
.ls-hero{ position:sticky; top:calc(46px + env(safe-area-inset-top,0px)); z-index:0; min-height:44vh; display:flex; align-items:center; justify-content:center; text-align:center; }
.ls-hero::before{ content:""; position:absolute; inset:-30% -20%; background:radial-gradient(55% 55% at 50% 35%, var(--accent-soft), transparent 72%); pointer-events:none; }
.ls-hero-in{ position:relative; padding:24px;
  transform:scale(calc(1 - min(var(--hp,0),1)*.12)) translateY(calc(min(var(--hp,0),1)*-16px));
  opacity:calc(1 - min(var(--hp,0),1)*.92);
  will-change:transform,opacity; }
.ls-hero-title{ font-size:var(--t-hero); margin:10px 0 8px; letter-spacing:-.03em; line-height:1.05; font-family:var(--font-display); font-weight:700; }
.ls-hero-meta{ display:flex; gap:10px; align-items:center; justify-content:center; }
.ls-hero-meta .bookmark-btn{ font-size:18px; }
.ls-scroll-hint{ margin-top:26px; font-size:20px; color:var(--text-dim); animation:lsHint 1.8s ease-in-out infinite; }
@keyframes lsHint{ 0%,100%{ transform:translateY(0); opacity:.5 } 50%{ transform:translateY(7px); opacity:1 } }
.ls-rail{ position:sticky; top:calc(52px + env(safe-area-inset-top,0px)); z-index:60; display:flex; align-items:center; gap:10px; padding:9px 16px; margin:0 0 6px; border-radius:var(--radius-full);
  background:var(--glass); -webkit-backdrop-filter:blur(20px) saturate(1.4); backdrop-filter:blur(20px) saturate(1.4); border:1px solid var(--glass-border); box-shadow:var(--shadow-sm); }
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))){ .ls-rail{ background:var(--surface); } }
.ls-rail-track{ flex:1; height:3px; border-radius:999px; background:var(--surface-2); overflow:hidden; }
.ls-rail-fill{ height:100%; width:0; background:var(--accent-1); box-shadow:0 0 8px var(--accent-glow); border-radius:999px; }
.ls-rail-dots{ display:flex; gap:6px; }
.ls-dot{ width:10px; height:10px; border-radius:50%; border:0; padding:0; background:var(--surface-3); cursor:pointer; transition:transform var(--dur-fast), background var(--dur-fast); }
.ls-dot:hover{ transform:scale(1.3); }
.ls-dot.done{ background:var(--success); }
.ls-dot.cur{ background:var(--accent-1); transform:scale(1.4); box-shadow:0 0 8px var(--accent-glow); }
.ls-dot.locked{ background:var(--surface-2); cursor:not-allowed; }
.ls-dot.locked:hover{ transform:none; }
.ls-dot.cp{ border-radius:3px; }
.ls-rail-count{ font-family:var(--font-dot); font-size:11px; color:var(--text-dim); letter-spacing:.08em; font-weight:700; }
.ls-chunks{ position:relative; z-index:1; display:flex; flex-direction:column; gap:36px; padding-top:8vh; padding-bottom:26vh; }
.ls-chunk{ position:relative; scroll-margin-top:118px; }
.ls-chunk-head{ margin:0 0 10px 4px; display:flex; flex-direction:column; gap:4px; }
.ls-chunk-title{ margin:0; font-size:var(--t-h2); letter-spacing:-.02em; font-family:var(--font-display); }
.ls-chunk-foot{ display:flex; align-items:center; gap:12px; margin-top:12px; padding:0 4px; flex-wrap:wrap; }
.ls-chunk-foot .spacer{ flex:1; }
.ls-gate-done{ color:var(--success); font-weight:700; font-size:13px; }
.ls-locked > *:not(.ls-lock-overlay){ filter:blur(9px) saturate(.6); pointer-events:none; user-select:none; }
.ls-lock-overlay{ position:absolute; inset:0; z-index:5; display:flex; align-items:flex-start; justify-content:center; padding-top:54px; }
.ls-lock-card{ display:flex; flex-direction:column; align-items:center; gap:4px; background:var(--glass); -webkit-backdrop-filter:blur(12px) saturate(1.3); backdrop-filter:blur(12px) saturate(1.3); border:1px solid var(--glass-border); padding:16px 28px; border-radius:var(--radius); box-shadow:var(--shadow); font-size:15px; }
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))){ .ls-lock-card{ background:var(--surface); } }
.ls-lock-card span{ font-size:12.5px; color:var(--text-dim); }
.ls-unlock{ animation:lsUnlock .8s var(--ease-out); }
@keyframes lsUnlock{ 0%{ filter:blur(9px); opacity:.35 } 100%{ filter:none; opacity:1 } }
@media (prefers-reduced-motion: reduce){
  .ls-hero{ position:static; min-height:0; }
  .ls-hero-in{ transform:none !important; opacity:1 !important; }
  .ls-scroll-hint{ display:none; }
  .ls-chunks{ padding-top:12px; }
  .ls-unlock{ animation:none; }
}
@media (max-width:560px){ .ls-hero{ min-height:34vh; } .ls-chunks{ gap:26px; } }
"""
s = s.replace(anchor, anchor + scrolly_css)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("phase2 applied; old js block", len(old), "-> new", len(new_js))
