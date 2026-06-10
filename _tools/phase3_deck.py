# Phase 3: Cards tab → 3D deck (stage + underlays + outcome-directed fling + filmstrip).
# All element ids (fc-reveal-btn, fc-reveal, fc-answer-box, fc-conf-area, fc-skip,
# fc-why-btn/box) and the wireConfidence/keyboard contracts are preserved.
import io

p = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
s = io.open(p, encoding="utf-8").read()

# ---- 1. cardsAdvance: outcome-directed 3D fling instead of flat slide ----
old_adv = '''  // Pack 1.2: directional slide between cards. Slide-out left → render → slide-in right.
  const area = document.getElementById("cards-area");
  const cardEl = area && area.querySelector(".drill-card");
  if (cardEl && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    cardEl.classList.add("fc-swap-out");
    setTimeout(() => {
      renderCardFace();
      const nextCardEl = area.querySelector(".drill-card");
      if (nextCardEl) { nextCardEl.classList.remove("fc-swap-out"); void nextCardEl.offsetWidth; nextCardEl.classList.add("fc-swap-in"); }
    }, 180);
  } else {
    renderCardFace();
  }
}'''
new_adv = '''  // PULSE deck: outcome-directed 3D fling — wrong flies left, sure flies up, rest fly right;
  // the next card promotes from the underlay stack (.fc-deal).
  const area = document.getElementById("cards-area");
  const cardEl = area && area.querySelector(".drill-card");
  const outcome = window._fcOutcome; window._fcOutcome = null;
  if (cardEl && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const dir = outcome === "wrong" ? "left" : (outcome === "right-sure" ? "up" : "right");
    cardEl.classList.add("fc-fling-" + dir);
    setTimeout(() => {
      renderCardFace();
      const nextCardEl = area.querySelector(".drill-card");
      if (nextCardEl) { void nextCardEl.offsetWidth; nextCardEl.classList.add("fc-deal"); }
    }, 300);
  } else {
    renderCardFace();
  }
}'''
assert old_adv in s
s = s.replace(old_adv, new_adv)

# ---- 2. renderCardFace: wrap in 3D stage with underlays + filmstrip ----
old_face = '''  area.innerHTML = `<div class="drill-card">
    ${tag}
    <div class="drill-cue">${teach ? "Learn" : "Recall"}</div>
    <div class="drill-recall-prompt">${flashPrompt(card)}</div>
    <div class="drill-say">${teach ? "Read it, predict the answer, then reveal to learn it." : "Recall the answer, then reveal to check."}</div>
    <button class="btn secondary" id="fc-reveal-btn">👁 Reveal answer</button>
    <div class="drill-reveal" id="fc-reveal"><div class="drill-answer-box" id="fc-answer-box"></div></div>
    ${whyBlock}
    <div id="fc-conf-area"></div>
    <button class="drill-skip-btn" id="fc-skip">skip for now →</button>
  </div>`;
  markRefContext(area);'''
new_face = '''  // underlay stack: the next two queue cards peek out from behind the active one
  const unders = [1, 2].map(k => {
    const uc = q[(cardsState.idx + k) % q.length];
    if (!uc || q.length <= k) return "";
    return `<div class="fc-under fc-u${k}" aria-hidden="true"><div class="fc-under-prompt">${flashPrompt(uc)}</div></div>`;
  }).join("");
  // session filmstrip: cards graded this sitting (latest first), scroll-snap row
  const hist = (cardsState.history || []);
  const stripHtml = hist.length ? `<div class="fc-strip-wrap"><span class="eyebrow">THIS SESSION · ${hist.length}</span>
    <div class="fc-strip" id="fc-strip">${hist.map(h => {
      const hc = FLASHCARDS.find(c => c.fid === h.fid);
      if (!hc) return "";
      return `<button class="fc-hist ${h.outcome === "wrong" ? "bad" : "good"}" data-hfid="${escapeAttr(h.fid)}" title="Peek">${h.outcome === "wrong" ? "✗" : "✓"} ${escapeHtml((hc.q || hc.a || "").replace(/<[^>]+>/g, "").slice(0, 38))}…</button>`;
    }).join("")}</div></div>` : "";
  area.innerHTML = `<div class="fc-stage">
    ${unders}
    <div class="drill-card">
    ${tag}
    <div class="drill-cue">${teach ? "Learn" : "Recall"}</div>
    <div class="drill-recall-prompt">${flashPrompt(card)}</div>
    <div class="drill-say">${teach ? "Read it, predict the answer, then reveal to learn it." : "Recall the answer, then reveal to check."}</div>
    <button class="btn secondary" id="fc-reveal-btn">👁 Reveal answer</button>
    <div class="drill-reveal" id="fc-reveal"><div class="drill-answer-box" id="fc-answer-box"></div></div>
    ${whyBlock}
    <div id="fc-conf-area"></div>
    <button class="drill-skip-btn" id="fc-skip">skip for now →</button>
  </div></div>${stripHtml}`;
  markRefContext(area);
  area.querySelectorAll(".fc-hist").forEach(b => b.addEventListener("click", () => {
    const hc = FLASHCARDS.find(c => c.fid === b.dataset.hfid);
    if (!hc) return;
    openQpModal(`<h2>📇 Card peek</h2>
      <div class="fc-peek-q">${hc.qHtml || escapeHtml(hc.q || "")}</div>
      <div class="fc-peek-a">${hc.aHtml || escapeHtml(hc.a || "")}</div>
      ${hc.why ? `<div class="fc-peek-why">${renderWhy(hc.why)}</div>` : ""}`);
  }));'''
assert old_face in s
s = s.replace(old_face, new_face)

# ---- 3. record outcome + history in onPick ----
old_pick = '''    wireConfidence(ca, { id: "fc:" + card.fid, type: "flash", wasWrong: false, onPick: (outcome) => {
      const LAP_SPACING = 3;'''
new_pick = '''    wireConfidence(ca, { id: "fc:" + card.fid, type: "flash", wasWrong: false, onPick: (outcome) => {
      const LAP_SPACING = 3;
      window._fcOutcome = outcome;                       // steers the fling direction
      cardsState.history = cardsState.history || [];
      cardsState.history.unshift({ fid: card.fid, outcome });
      if (cardsState.history.length > 40) cardsState.history.length = 40;'''
assert old_pick in s
s = s.replace(old_pick, new_pick)

# ---- 4. CSS: deck stage, underlays, fling, deal, filmstrip ----
anchor = "@media (max-width:560px){ .ls-hero{ min-height:34vh; } .ls-chunks{ gap:26px; } }\n"
assert anchor in s
deck_css = """
/* ===== Cards 3D deck (PULSE) ===== */
.fc-stage{ position:relative; perspective:1400px; margin-bottom:14px; }
.fc-stage .drill-card{ position:relative; z-index:2; margin-bottom:0; transform-style:preserve-3d; }
.fc-under{ position:absolute; inset:0; z-index:0; border:1px solid var(--border); border-radius:var(--radius); background:var(--surface); box-shadow:var(--shadow-sm); overflow:hidden; pointer-events:none; display:flex; align-items:flex-start; justify-content:center; padding:22px 26px; }
.fc-u1{ transform:translateY(14px) scale(.955); opacity:.55; }
.fc-u2{ transform:translateY(27px) scale(.91); opacity:.3; }
.fc-under-prompt{ filter:blur(4px); font-size:17px; color:var(--text-dim); max-width:600px; user-select:none; }
.fc-fling-right{ animation:fcFlingRight .42s var(--ease-in-out) forwards; }
.fc-fling-left{ animation:fcFlingLeft .42s var(--ease-in-out) forwards; }
.fc-fling-up{ animation:fcFlingUp .42s var(--ease-in-out) forwards; }
@keyframes fcFlingRight{ to{ transform:translateX(115%) rotateZ(9deg) rotateY(16deg); opacity:0; } }
@keyframes fcFlingLeft{ to{ transform:translateX(-115%) rotateZ(-9deg) rotateY(-16deg); opacity:0; } }
@keyframes fcFlingUp{ to{ transform:translateY(-55%) scale(.82) rotateX(24deg); opacity:0; } }
.fc-deal{ animation:fcDeal .34s var(--ease-spring); }
@keyframes fcDeal{ 0%{ transform:translateY(14px) scale(.955); opacity:.55; } 100%{ transform:none; opacity:1; } }
.fc-strip-wrap{ margin:10px 2px 14px; display:flex; flex-direction:column; gap:6px; }
.fc-strip{ display:flex; gap:8px; overflow-x:auto; scroll-snap-type:x proximity; padding:2px 2px 8px; -webkit-overflow-scrolling:touch; scrollbar-width:thin; }
.fc-hist{ scroll-snap-align:start; flex:0 0 auto; max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-full); padding:7px 13px; font-size:12px; font-weight:600; color:var(--text-dim); cursor:pointer; transition:transform var(--dur-fast), border-color var(--dur-fast); }
.fc-hist:hover{ transform:translateY(-1px); border-color:var(--accent-line); }
.fc-hist.good{ box-shadow:inset 3px 0 0 0 var(--success); }
.fc-hist.bad{ box-shadow:inset 3px 0 0 0 var(--danger); }
.fc-peek-q{ font-weight:700; font-size:16px; margin-bottom:10px; }
.fc-peek-a{ background:color-mix(in srgb, var(--accent-1) 8%, var(--surface)); border:1px solid var(--accent-line); border-radius:10px; padding:10px 14px; margin-bottom:10px; }
.fc-peek-why{ font-size:13px; color:var(--text-dim); }
@media (prefers-reduced-motion: reduce){
  .fc-fling-right,.fc-fling-left,.fc-fling-up,.fc-deal{ animation:none; }
  .fc-under{ display:none; }
}
"""
s = s.replace(anchor, anchor + deck_css)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("phase3 deck applied")
