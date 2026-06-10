# Phase 5: hub (index.html) → PULSE. Replaces the whole <style> block, removes Google
# Fonts links, patches JS (light/dark prefs, de-themed copy, per-course accents, PM module).
import io
import re

HUB = r"C:\Users\izzyp\src\nursingduo\index.html"
TPL = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
s = io.open(HUB, encoding="utf-8").read()
tpl = io.open(TPL, encoding="utf-8").read()

# ---- pull the byte-identical PULSE CORE + PM sentinel blocks from the template ----
core = tpl[tpl.index("/* ═══ PULSE CORE v1"):tpl.index("/* ═══ /PULSE CORE ═══ */") + len("/* ═══ /PULSE CORE ═══ */")]
pm = tpl[tpl.index("/* ═══ PULSE MOTION v1"):tpl.index("/* ═══ /PULSE MOTION ═══ */") + len("/* ═══ /PULSE MOTION ═══ */")]

HUB_CSS = """
/* ============================================================
   NursingDuo hub — PULSE design system
   Core tokens live in the sentinel block above (source of truth:
   template-v2.html — keep byte-identical).
   ============================================================ */
:root {
  --accent-1: #0a84ff;            /* hub identity: clinical blue */
  --accent-2: #5ac8fa;
  --accent-soft: color-mix(in srgb, var(--accent-1) 12%, var(--bg));
  --accent-glow: color-mix(in srgb, var(--accent-1) 45%, transparent);
  --accent-line: color-mix(in srgb, var(--accent-1) 35%, var(--border));
}
[data-theme="dark"] {
  --accent-1: #409cff;
  --accent-2: #7dd3fc;
  --accent-soft: color-mix(in srgb, var(--accent-1) 14%, var(--bg));
  --accent-glow: color-mix(in srgb, var(--accent-1) 45%, transparent);
  --accent-line: color-mix(in srgb, var(--accent-1) 35%, var(--border));
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: var(--font-body);
  font-size: var(--t-body);
  background: var(--bg);
  color: var(--text);
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  max-width: 760px;
  margin: 0 auto;
  padding: 28px 18px calc(60px + env(safe-area-inset-bottom, 0px));
  position: relative;
}
body::before { content: ""; position: fixed; inset: -20% -30% auto; height: 70vh; background: radial-gradient(55% 60% at 50% 0%, var(--accent-soft), transparent 70%); pointer-events: none; z-index: -1; }

/* account chip */
.chip { position: fixed; top: calc(12px + env(safe-area-inset-top, 0px)); right: 14px; z-index: 50; display: flex; align-items: center; gap: 6px;
  background: var(--glass); -webkit-backdrop-filter: blur(16px) saturate(1.4); backdrop-filter: blur(16px) saturate(1.4);
  border: 1px solid var(--glass-border); border-radius: var(--radius-full); padding: 5px 6px 5px 13px; box-shadow: var(--shadow-sm); }
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) { .chip { background: var(--surface); } }
.chip-user { font-family: var(--font-dot); font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--text-dim); }
.chip button { background: var(--surface-2); border: 0; color: var(--text); width: 28px; height: 28px; border-radius: 50%; cursor: pointer; font-size: 13px; transition: transform var(--dur-fast), background var(--dur-fast); }
.chip button:hover { background: var(--surface-3); transform: rotate(45deg); }

/* brand */
.brand-wrap { text-align: center; margin: 26px 0 30px; }
.brand { font-family: var(--font-display); font-size: var(--t-hero); font-weight: 700; letter-spacing: -.04em; margin: 0; line-height: 1; }
.brand-initial { color: var(--accent-1); cursor: pointer; display: inline-block; transition: transform var(--dur-fast) var(--ease-spring); }
.brand-initial:hover { transform: scale(1.08) rotate(-3deg); }
.brand-sub { font-family: var(--font-dot); font-size: 11px; font-weight: 700; letter-spacing: .34em; text-transform: uppercase; color: var(--text-dim); margin-top: 10px; }

/* hero */
.hero { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 22px 22px 18px; box-shadow: var(--shadow); cursor: pointer; transition: transform var(--dur-fast), box-shadow var(--dur-fast), border-color var(--dur-fast); position: relative; overflow: hidden; }
.hero:hover { transform: translateY(-2px); border-color: var(--accent-line); box-shadow: var(--shadow-lg); }
.hero::before { content: ""; position: absolute; inset: -60% -20% auto; height: 120%; background: radial-gradient(50% 55% at 30% 20%, var(--accent-soft), transparent 70%); pointer-events: none; }
.hero-grid { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; position: relative; }
.hero-left { display: flex; align-items: center; gap: 16px; }
.hero-avatar { width: 64px; height: 64px; border-radius: 50%; background: var(--surface-2); border: 2px solid var(--accent-line); display: flex; align-items: center; justify-content: center; font-size: 30px; flex-shrink: 0; cursor: pointer; user-select: none; box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent-1) 8%, transparent); transition: box-shadow var(--dur); }
.hero-avatar.streak-tier-1 { box-shadow: 0 0 0 4px color-mix(in srgb, var(--warn) 22%, transparent); }
.hero-avatar.streak-tier-2 { box-shadow: 0 0 0 4px color-mix(in srgb, var(--warn) 35%, transparent), 0 0 18px -2px var(--warn); }
.hero-avatar.streak-tier-3 { box-shadow: 0 0 0 4px color-mix(in srgb, var(--danger) 35%, transparent), 0 0 26px -2px var(--warn); }
.hero-avatar.bump { animation: avatarBump .4s var(--ease-spring); }
@keyframes avatarBump { 0% { transform: scale(1); } 45% { transform: scale(1.16) rotate(-5deg); } 100% { transform: scale(1); } }
.hero-level { font-family: var(--font-dot); font-size: 11px; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: var(--text-dim); }
.hero-title { font-family: var(--font-display); font-size: 24px; font-weight: 700; letter-spacing: -.02em; line-height: 1.15; }
.hero-rank-tag { font-size: 11.5px; color: var(--text-dim); margin-top: 2px; }
.hero-right { display: flex; align-items: center; gap: 20px; }
.hero-xp-block { text-align: right; }
.hero-xp-num { font-family: var(--font-dot); font-size: 30px; font-weight: 700; color: var(--accent-1); line-height: 1; }
.hero-xp-sub { font-family: var(--font-dot); font-size: 9.5px; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; color: var(--text-dim); margin-top: 5px; }
.hero-streak { display: flex; flex-direction: column; align-items: center; gap: 1px; opacity: .55; }
.hero-streak.live { opacity: 1; }
.hero-streak-flame { font-size: 20px; }
.hero-streak.live .hero-streak-flame { animation: flameFlicker 1.6s ease-in-out infinite; }
@keyframes flameFlicker { 0%,100% { transform: scale(1); } 50% { transform: scale(1.18); } }
.hero-streak-num { font-family: var(--font-dot); font-size: 18px; font-weight: 700; }
.hero-streak-lbl { font-family: var(--font-dot); font-size: 8.5px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--text-dim); }

.xp-bar-wrap { margin-top: 16px; position: relative; }
.xp-bar { height: 6px; background: var(--surface-2); border-radius: 999px; overflow: hidden; }
.xp-bar-fill { height: 100%; background: var(--accent-1); box-shadow: 0 0 10px var(--accent-glow); border-radius: 999px; transition: width .8s var(--ease-out); }
.xp-bar-fill.full { background: var(--gold); box-shadow: 0 0 12px color-mix(in srgb, var(--gold) 55%, transparent); }
.xp-bar-labels { display: flex; justify-content: space-between; font-size: 11.5px; color: var(--text-dim); margin-top: 7px; }
.xp-bar-labels strong { color: var(--text); font-family: var(--font-dot); font-weight: 700; letter-spacing: .04em; }

.week-strip { margin-top: 16px; border-top: 1px solid var(--border); padding-top: 12px; position: relative; }
.week-strip-title { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }
.week-strip-title span { font-family: var(--font-dot); font-size: 10px; font-weight: 700; letter-spacing: .2em; text-transform: uppercase; color: var(--text-dim); }
.week-strip-title em { font-style: normal; font-size: 10.5px; color: var(--text-dim); opacity: .7; }
.week-bars { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }
.wb { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.wb-track { width: 100%; height: 38px; background: var(--surface-2); border-radius: 6px; display: flex; align-items: flex-end; overflow: hidden; }
.wb-bar { width: 100%; background: var(--surface-3); border-radius: 6px 6px 0 0; transition: height .6s var(--ease-out); }
.wb.on .wb-bar { background: var(--accent-1); box-shadow: 0 0 8px var(--accent-glow); }
.wb.today .wb-bar { background: var(--gold); box-shadow: 0 0 10px color-mix(in srgb, var(--gold) 50%, transparent); }
.wb.fresh .wb-bar { animation: wbGrow .7s var(--ease-out) backwards; }
@keyframes wbGrow { from { height: 0 !important; } }
.wb-label { font-family: var(--font-dot); font-size: 9px; font-weight: 700; letter-spacing: .1em; color: var(--text-dim); }
.wb.today .wb-label { color: var(--gold); }

/* section headers */
.section-head { font-family: var(--font-dot); font-size: 11px; font-weight: 700; letter-spacing: .28em; text-transform: uppercase; color: var(--text-dim); display: flex; align-items: center; gap: 12px; margin: 30px 0 12px; }
.section-head::after { content: ""; flex: 1; height: 1px; background: var(--border); }
.section-head .glyph { display: none; }

/* today's set */
.quests { display: flex; flex-direction: column; gap: 10px; }
.quest { display: flex; align-items: center; justify-content: space-between; gap: 14px; background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--qa, var(--accent-1)); border-radius: var(--radius); padding: 14px 18px; text-decoration: none; color: var(--text); box-shadow: var(--shadow-sm); transition: transform var(--dur-fast), box-shadow var(--dur-fast), border-color var(--dur-fast); }
a.quest:hover { transform: translateY(-2px); box-shadow: 0 10px 28px -10px color-mix(in srgb, var(--qa, var(--accent-1)) 45%, transparent); border-color: var(--qa, var(--accent-1)); }
.quest-info { display: flex; align-items: center; gap: 13px; min-width: 0; }
.quest-icon { font-size: 24px; flex-shrink: 0; }
.quest-name { font-family: var(--font-display); font-weight: 700; font-size: 15.5px; letter-spacing: -.01em; }
.quest-meta { display: flex; align-items: center; gap: 7px; font-size: 12.5px; color: var(--text-dim); margin-top: 2px; }
.quest-due-pill { background: color-mix(in srgb, var(--qa, var(--accent-1)) 12%, transparent); color: var(--qa, var(--accent-1)); border-radius: var(--radius-full); padding: 1px 10px; font-size: 12px; font-weight: 600; }
.quest-due-pill strong { font-family: var(--font-dot); font-weight: 700; }
.quest-clear { font-size: 12.5px; color: var(--success); font-weight: 700; flex-shrink: 0; }
.quest-go { font-size: 13px; font-weight: 700; color: var(--qa, var(--accent-1)); flex-shrink: 0; display: flex; align-items: center; gap: 5px; }
.quest-go .arrow { transition: transform var(--dur-fast); }
a.quest:hover .quest-go .arrow { transform: translateX(3px); }
.quest-empty { display: flex; align-items: center; gap: 10px; justify-content: center; padding: 22px; color: var(--text-dim); font-size: 14px; background: var(--surface); border: 1px dashed var(--border); border-radius: var(--radius); }
.quest-empty .emoji { font-size: 20px; }

/* course tiles */
.courses-grid { display: flex; flex-direction: column; gap: 12px; perspective: 1100px; }
.course { display: flex; align-items: center; gap: 15px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 17px 18px; text-decoration: none; color: var(--text); box-shadow: var(--shadow-sm); position: relative; overflow: hidden;
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg)); transition: transform .18s var(--ease-out), box-shadow var(--dur-fast), border-color var(--dur-fast); will-change: transform; }
.course:hover { border-color: var(--ca, var(--accent-line)); box-shadow: 0 14px 38px -14px color-mix(in srgb, var(--ca, var(--accent-1)) 55%, transparent); }
.course::before { content: ""; position: absolute; inset: 0; background: radial-gradient(60% 120% at 0% 50%, color-mix(in srgb, var(--ca, var(--accent-1)) 9%, transparent), transparent 60%); pointer-events: none; }
.course-accent { position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--ca, var(--accent-1)); box-shadow: 0 0 12px color-mix(in srgb, var(--ca, var(--accent-1)) 60%, transparent); }
.course-icon { font-size: 28px; flex-shrink: 0; }
.course-body { flex: 1; min-width: 0; }
.course-name { font-family: var(--font-display); font-size: 17px; font-weight: 700; letter-spacing: -.01em; }
.course-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-dim); margin-top: 3px; flex-wrap: wrap; }
.course-meta .dot { width: 3px; height: 3px; border-radius: 50%; background: var(--text-dim); opacity: .5; }
.course-id-mono { font-family: var(--font-dot); letter-spacing: .08em; }
.course-right { text-align: right; flex-shrink: 0; }
.course-xp { font-family: var(--font-dot); font-size: 19px; font-weight: 700; color: var(--ca, var(--accent-1)); }
.course-xp .sub { font-size: 10px; color: var(--text-dim); margin-left: 3px; }
.course-bar { width: 86px; height: 4px; background: var(--surface-2); border-radius: 999px; overflow: hidden; margin-top: 7px; margin-left: auto; }
.course-bar-fill { height: 100%; background: var(--ca, var(--accent-1)); border-radius: 999px; box-shadow: 0 0 6px color-mix(in srgb, var(--ca, var(--accent-1)) 60%, transparent); }
.course.soon { opacity: .55; }
.course-lock { font-size: 18px; }
.course-sealed { display: block; font-family: var(--font-dot); font-size: 9.5px; letter-spacing: .12em; text-transform: uppercase; color: var(--text-dim); margin-top: 3px; }

.foot-mark { text-align: center; font-family: var(--font-dot); font-size: 10px; font-weight: 700; letter-spacing: .3em; text-transform: uppercase; color: var(--text-dim); opacity: .65; margin-top: 44px; display: flex; align-items: center; justify-content: center; gap: 10px; }
.foot-mark .glyph { color: var(--accent-1); }

/* modals */
.modal-bg { position: fixed; inset: 0; z-index: 200; background: rgba(0,0,0,.5); -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px); display: flex; align-items: center; justify-content: center; padding: 20px; animation: modalIn var(--dur-fast) ease; overflow-y: auto; }
@keyframes modalIn { from { opacity: 0; } }
.modal-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 26px 24px; width: 100%; max-width: 420px; max-height: 88vh; overflow-y: auto; box-shadow: var(--shadow-lg); position: relative; animation: cardIn var(--dur) var(--ease-out); }
@keyframes cardIn { from { opacity: 0; transform: translateY(16px) scale(.98); } }
.modal-title { font-family: var(--font-display); font-size: 21px; font-weight: 700; letter-spacing: -.02em; margin: 0 0 6px; display: flex; align-items: center; gap: 9px; }
.modal-title .glyph { color: var(--accent-1); }
.modal-desc { font-size: 13.5px; color: var(--text-dim); margin-bottom: 18px; }
.modal-hint { font-size: 12px; color: var(--text-dim); margin-top: 14px; line-height: 1.5; }
.modal-close { position: absolute; top: 14px; right: 14px; background: var(--surface-2); border: 0; color: var(--text); width: 30px; height: 30px; border-radius: 50%; font-size: 16px; cursor: pointer; }
.modal-close:hover { background: var(--surface-3); }
.modal-card label { display: block; font-family: var(--font-dot); font-size: 10.5px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 14px; }
.modal-card label input { display: block; width: 100%; margin-top: 6px; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); font: 600 16px/1.3 var(--font-body); padding: 11px 13px; letter-spacing: normal; text-transform: none; }
.modal-card label input:focus { outline: none; border-color: var(--accent-1); box-shadow: 0 0 0 3px var(--accent-glow); }
.btns { display: flex; gap: 10px; margin-top: 6px; }
.btn-primary { flex: 1; background: var(--accent-1); color: #fff; border: 0; border-radius: 13px; padding: 13px 20px; font: 700 15px/1 var(--font-display); cursor: pointer; box-shadow: 0 3px 0 color-mix(in srgb, var(--accent-1) 58%, #000); transition: filter var(--dur-fast), transform .07s, box-shadow .07s; }
.btn-primary:hover { filter: brightness(1.07); }
.btn-primary:active { transform: translateY(3px); box-shadow: none; }
.btn-ghost { background: transparent; color: var(--text-dim); border: 1px solid var(--border); border-radius: 13px; padding: 11px 18px; font: 700 14px/1 var(--font-display); cursor: pointer; }
.btn-ghost:hover { color: var(--text); border-color: var(--text-dim); }

.opt-group { margin-bottom: 18px; }
.opt-group-label { font-family: var(--font-dot); font-size: 10.5px; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 9px; }
.opt-list { display: flex; flex-wrap: wrap; gap: 8px; }
.opt { display: flex; align-items: center; gap: 7px; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-full); padding: 8px 14px; cursor: pointer; font-size: 13.5px; font-weight: 600; transition: border-color var(--dur-fast), background var(--dur-fast); }
.opt:has(input:checked) { border-color: var(--accent-1); background: color-mix(in srgb, var(--accent-1) 10%, var(--surface)); color: var(--accent-1); }
.opt input { accent-color: var(--accent-1); margin: 0; }
.opt.locked { opacity: .45; cursor: not-allowed; }
.opt-sub { font-size: 10px; color: var(--text-dim); }

/* stats modal */
.stats-hero { display: flex; align-items: center; gap: 15px; padding-bottom: 16px; border-bottom: 1px solid var(--border); margin-bottom: 14px; }
.stats-hero-avatar { width: 54px; height: 54px; border-radius: 50%; background: var(--surface-2); border: 2px solid var(--accent-line); display: flex; align-items: center; justify-content: center; font-size: 26px; }
.stats-hero-rank { font-family: var(--font-dot); font-size: 10px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--text-dim); }
.stats-hero-title { font-family: var(--font-display); font-size: 20px; font-weight: 700; }
.stats-hero-sub { font-size: 12.5px; color: var(--text-dim); }
.stats-section { padding: 11px 0; border-bottom: 1px solid var(--border); }
.stats-section:last-child { border-bottom: 0; }
.stats-section-label { font-family: var(--font-dot); font-size: 10px; font-weight: 700; letter-spacing: .2em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 7px; }
.stat-row { display: flex; align-items: baseline; justify-content: space-between; gap: 14px; padding: 4px 0; font-size: 14px; }
.stat-row .lbl { color: var(--text-dim); }
.stat-row .val { font-family: var(--font-dot); font-weight: 700; letter-spacing: .02em; }
.stat-row .val .sub { font-family: var(--font-body); font-weight: 500; font-size: 11.5px; color: var(--text-dim); margin-left: 6px; }
.stat-box-bar { display: flex; gap: 5px; align-items: flex-end; height: 44px; margin: 10px 0 4px; }
.stat-box-seg { flex: 1; height: 100%; background: var(--surface-2); border-radius: 5px; display: flex; align-items: flex-end; overflow: hidden; }
.stat-box-seg .fill { width: 100%; background: var(--accent-1); border-radius: 5px 5px 0 0; min-height: 2px; }
.stat-box-seg:nth-child(1) .fill { background: var(--danger); }
.stat-box-seg:nth-child(2) .fill { background: var(--warn); }
.stat-box-seg:nth-child(3) .fill { background: var(--info); }
.stat-box-seg:nth-child(4) .fill { background: var(--accent-1); }
.stat-box-seg:nth-child(5) .fill { background: var(--success); }
.stat-box-labels { display: flex; gap: 5px; }
.stat-box-labels span { flex: 1; text-align: center; font-size: 9.5px; color: var(--text-dim); display: flex; flex-direction: column; }
.stat-box-labels strong { font-family: var(--font-dot); font-size: 11px; color: var(--text); }

/* sparkle + confetti */
.brand-sparkle { position: fixed; z-index: 300; pointer-events: none; color: var(--accent-1); font-size: 14px; animation: sparkleFly .9s var(--ease-out) forwards; }
@keyframes sparkleFly { to { transform: translate(var(--dx, 0), var(--dy, 0)) scale(.4) rotate(120deg); opacity: 0; } }
.confetti-piece { position: fixed; top: -20px; z-index: 300; pointer-events: none; }
@keyframes confetti-fall { to { transform: translateY(110vh) rotate(680deg); opacity: .15; } }

@media (max-width: 520px) {
  .hero-grid { flex-direction: column; align-items: flex-start; }
  .hero-right { width: 100%; justify-content: space-between; flex-direction: row-reverse; }
  .hero-xp-block { text-align: left; }
  .brand { font-size: clamp(30px, 11vw, 44px); }
}
@media (prefers-reduced-motion: reduce) {
  .hero-streak.live .hero-streak-flame, .wb.fresh .wb-bar, .brand-sparkle, .confetti-piece { animation: none !important; }
  .course { transform: none !important; }
}
"""

# ---- 1. head: drop Google Fonts links + old theme-color ----
s = s.replace('<link rel="preconnect" href="https://fonts.googleapis.com">\n', "")
s = s.replace('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n', "")
s = re.sub(r'<link href="https://fonts\.googleapis\.com/css2[^>]*>\n', "", s)
s = s.replace('<meta name="theme-color" content="#f1e6c8">', '<meta name="theme-color" content="#050506">')

# ---- 2. replace the entire <style> block ----
a = s.index("<style>")
b = s.index("</style>") + len("</style>")
s = s[:a] + "<style>\n" + core + "\n" + HUB_CSS + "</style>" + s[b:]

# ---- 3. PM module before main script ----
s = s.replace("<script>\n/* ===== Theme system: visual + rank ladder ===== */",
              "<script>\n" + pm + "\n</script>\n<script>\n/* ===== Theme system: visual + rank ladder ===== */")

# ---- 4. JS patches ----
def rep(old, new, what):
    global s
    assert old in s, "MISSING: " + what
    s = s.replace(old, new)

# rank ladders: keep nursing + generic
rep("""  naruto: [
    [1, "Academy Student"], [4, "Genin"], [10, "Chunin"],
    [18, "Jonin"], [28, "Sannin"], [40, "Hokage"],
  ],
  onepiece: [
    [1, "Cabin Boy"], [4, "Pirate"], [10, "First Mate"],
    [18, "Captain"], [28, "Yonko"], [40, "Pirate King"],
  ],
};""", "};", "anime ladders")
rep("""const RANK_LABELS = {
  nursing:  "Nursing path",
  generic:  "Generic RPG",
  naruto:   "Hokage road",
  onepiece: "Pirate King",
};""", """const RANK_LABELS = {
  nursing:  "Nursing path",
  generic:  "Generic RPG",
};""", "rank labels")

# visual themes: light/dark only
a2 = s.index("const VISUAL_THEMES = {")
b2 = s.index("const PREF_KEY")
s = s[:a2] + """const VISUAL_THEMES = { dark: "Dark", light: "Light" };
const VISUAL_LOCKED = {};

""" + s[b2:]

# prefs: migrate any legacy theme value to dark
rep("""    const p = JSON.parse(localStorage.getItem(PREF_KEY) || "{}");
    return { theme: p.theme || "cozy", ranks: p.ranks || "nursing" };
  } catch { return { theme: "cozy", ranks: "nursing" }; }""",
    """    const p = JSON.parse(localStorage.getItem(PREF_KEY) || "{}");
    const theme = p.theme === "light" ? "light" : "dark";   // legacy codex themes → dark
    const ranks = (p.ranks === "generic") ? "generic" : "nursing";
    return { theme, ranks };
  } catch { return { theme: "dark", ranks: "nursing" }; }""", "prefs migrate")

# applyTheme: data-theme + static avatar
rep("""function applyTheme() {
  const p = getPrefs();
  if (p.theme && p.theme !== "cozy") document.body.setAttribute("data-theme", p.theme);
  else document.body.removeAttribute("data-theme");
  const icon = THEME_HERO_ICON[p.theme] || THEME_HERO_ICON.cozy;
  const iconEl = document.getElementById("heroAvatar");
  if (iconEl) iconEl.textContent = icon;
  const pathTag = document.getElementById("heroPathTag");
  if (pathTag) pathTag.textContent = (RANK_LABELS[p.ranks] || "Nursing path").toLowerCase();
}""",
    """function applyTheme() {
  const p = getPrefs();
  document.body.setAttribute("data-theme", p.theme === "light" ? "light" : "dark");
  const pathTag = document.getElementById("heroPathTag");
  if (pathTag) pathTag.textContent = (RANK_LABELS[p.ranks] || "Nursing path").toLowerCase();
}""", "applyTheme")

# openStats hero icon
rep('  const heroIcon = THEME_HERO_ICON[prefs.theme] || "⚖️";', '  const heroIcon = "🩺";', "stats hero icon")

# courses: per-course accents
rep("""const COURSES = [
  { id: "ns250", name: "Med-Surg",          storageKey: "quizpage:ns250medsurg-master",         href: "/ns250", status: "live", icon: "🩺" },
  { id: "ns216", name: "Maternal-Newborn",  storageKey: "quizpage:ns216maternalnewborn-master", href: "/ns216", status: "live", icon: "🍼" },
  { id: "ns221", name: "Pharmacology",      storageKey: "quizpage:ns221pharmacology-master",    href: "/ns221", status: "live", icon: "💊" },
];""",
    """const COURSES = [
  { id: "ns250", name: "Med-Surg",          storageKey: "quizpage:ns250medsurg-master",         href: "/ns250", status: "live", icon: "🩺", accent: "#dc2626" },
  { id: "ns216", name: "Maternal-Newborn",  storageKey: "quizpage:ns216maternalnewborn-master", href: "/ns216", status: "live", icon: "🍼", accent: "#0d9488" },
  { id: "ns221", name: "Pharmacology",      storageKey: "quizpage:ns221pharmacology-master",    href: "/ns221", status: "live", icon: "💊", accent: "#7c3aed" },
];
// dark mode lifts course hues exactly like the masters do
function courseAccent(c) {
  const dark = document.body.getAttribute("data-theme") !== "light";
  return dark ? `color-mix(in srgb, ${c.accent} 72%, #ffffff 28%)` : c.accent;
}""", "courses accents")

# quest copy + accent var
rep('    return `<a class="quest" href="${r.c.href}#tab=review">',
    '    return `<a class="quest" href="${r.c.href}#tab=review" style="--qa:${courseAccent(r.c)}">', "quest accent")
rep('      <span class="quest-go">pursue<span class="arrow">→</span></span>',
    '      <span class="quest-go">review<span class="arrow">→</span></span>', "quest go copy")
rep('No realms unlocked yet.', "No courses yet.", "quest empty copy")
rep('All quests cleared. Return tomorrow, brave one.', "All clear — nothing due. See you tomorrow.", "all clear copy")
rep('<div class="quest-meta">no quests today</div>', '<div class="quest-meta">nothing due</div>', "no quests copy")

# course tile accent + copy
rep("""      <a class="course${isSoon ? " soon" : ""}" href="${isSoon ? "#" : c.href}"${isSoon ? ' onclick="return false"' : ""}>""",
    """      <a class="course${isSoon ? " soon" : ""}" href="${isSoon ? "#" : c.href}"${isSoon ? ' onclick="return false"' : ""} style="--ca:${courseAccent(c)}">""", "course accent")
rep('${c.id.toUpperCase()} · sealed', "${c.id.toUpperCase()} · soon", "sealed copy")
rep('<span class="course-lock">🔒</span><span class="course-sealed">sealed scroll</span>',
    '<span class="course-lock">🔒</span><span class="course-sealed">coming soon</span>', "sealed scroll copy")

# auth modal copy
rep('<h2 class="modal-title"><span class="glyph">☁</span>Enter the realm</h2>', '<h2 class="modal-title"><span class="glyph">✦</span>Sign in</h2>', "auth title")
rep('The PIN does not match. Try again, traveler.', "That PIN didn't match — try again.", "auth wrong copy")
rep('<button class="btn-primary" id="cs_ok">Begin</button>', '<button class="btn-primary" id="cs_ok">Sign in</button>', "auth btn")

# settings copy
rep('<div class="modal-desc">Customize your study realm.</div>', '<div class="modal-desc">Appearance and account.</div>', "settings copy")
rep('<div class="opt-group-label">Visual theme</div>', '<div class="opt-group-label">Theme</div>', "settings theme label")

# brand + footer copy
rep('<div class="brand-sub">a study quest log</div>', '<div class="brand-sub">Study System</div>', "brand sub")
rep("""<div class="foot-mark">
  <span class="glyph">✦</span>
  may your reviews be many and your forgetting few
  <span class="glyph">✦</span>
</div>""",
    """<div class="foot-mark">
  <span class="glyph">✦</span>
  spaced repetition · daily
  <span class="glyph">✦</span>
</div>""", "foot mark")

# hero avatar: static mark (applyTheme no longer sets it)
rep('<div class="hero-avatar" id="heroAvatar">⚖️</div>', '<div class="hero-avatar" id="heroAvatar">🩺</div>', "hero avatar")

# section heads
rep('<div class="section-head"><span class="glyph"></span>today\'s adventures<span class="glyph"></span></div>',
    '<div class="section-head">Today</div>', "today head")
rep('<div class="section-head"><span class="glyph"></span>your studies<span class="glyph"></span></div>',
    '<div class="section-head">Courses</div>', "courses head")

# theme shuffle easter egg → light/dark flicker
rep('  const themes = ["cozy", "naruto", "onepiece"];', '  const themes = ["dark", "light"];', "shuffle themes")
rep("""  let i = 0;
  const tick = setInterval(() => {
    document.body.removeAttribute("data-theme");
    const t = themes[i % themes.length];
    if (t !== "cozy") document.body.setAttribute("data-theme", t);
    i++;""",
    """  let i = 0;
  const tick = setInterval(() => {
    document.body.setAttribute("data-theme", themes[i % themes.length]);
    i++;""", "shuffle tick")
rep("""      // Restore user's actual theme
      if (orig && orig !== "cozy") document.body.setAttribute("data-theme", orig);
      else document.body.removeAttribute("data-theme");""",
    """      // Restore user's actual theme
      applyTheme();""", "shuffle restore")
rep('  const orig = getPrefs().theme || "cozy";\n', "", "shuffle orig var")

# confetti palette
rep('  const palette = ["var(--gold)", "var(--amber)", "var(--crimson)", "var(--moss)", "var(--teal)"];',
    '  const palette = ["var(--gold)", "var(--accent-1)", "var(--accent-2)", "var(--success)", "var(--danger)"];', "confetti palette")

# render(): stagger reveal via PM
rep("""function render(snapshot) {
  lastSnapshot = snapshot || lastSnapshot;
  renderHero(lastSnapshot);
  renderTodaysSet(lastSnapshot.courses || {});
  renderCourses(lastSnapshot.courses || {});
  renderChip();""",
    """function render(snapshot) {
  lastSnapshot = snapshot || lastSnapshot;
  renderHero(lastSnapshot);
  renderTodaysSet(lastSnapshot.courses || {});
  renderCourses(lastSnapshot.courses || {});
  renderChip();
  // PULSE: stagger-reveal quests + course tiles
  document.querySelectorAll("#todaysSet .quest, #courses .course").forEach(el => el.setAttribute("data-rv", ""));
  PM.reveal(document.body);""", "render reveal")

io.open(HUB, "w", encoding="utf-8", newline="\n").write(s)
print("hub rewritten:", len(s), "bytes")
