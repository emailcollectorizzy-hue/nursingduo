# One-shot: replace the DUOLINGO SKIN override layer with the PULSE component skin.
import io

p = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
s = io.open(p, encoding="utf-8").read()
start = s.index("/* ===================================================================\n   DUOLINGO SKIN")
end = s.index("input:focus,select:focus{ border-color:var(--du-blue) !important; outline:none; }")
end = s.index("\n", end) + 1
old = s[start:end]
assert "--du-green:#58cc02" in old and "THE PATH" in old, "unexpected block"

new = """/* ===================================================================
   PULSE COMPONENT SKIN — final override layer (cascade-last; no JS/contract touch)
   Apple depth + Nothing dot-matrix detail + Duolingo juice on press
   =================================================================== */
:root{
  /* legacy du-* aliases — older selectors/template strings may still reference them */
  --du-green:var(--success); --du-green-edge:color-mix(in srgb, var(--success) 60%, #000); --du-green-hi:var(--success);
  --du-blue:var(--info);  --du-blue-edge:color-mix(in srgb, var(--info) 60%, #000);
  --du-orange:#ff9f0a; --du-red:var(--danger); --du-gold:var(--gold);
  --du-wrong-bg:color-mix(in srgb, var(--danger) 12%, var(--surface));
  --du-wrong-tx:var(--danger);
  --du-right-bg:color-mix(in srgb, var(--success) 14%, var(--surface));
  --du-right-tx:var(--success);
}
body{ background:var(--bg); color:var(--text); font-weight:500; -webkit-font-smoothing:antialiased; }
h1,h2,h3,.lesson-title,.path-title,.shop-card h3,.ach-card h3,.quests-card h3{ font-weight:700; letter-spacing:-.02em; font-family:var(--font-display); }

/* Header chips — glass monitor readouts (PULSE base header stays untouched) */
.hdr-chip,.streak,.hdr-hearts{ background:var(--surface-2); color:var(--text); font-weight:800; border-radius:var(--radius-full); padding:6px 11px; }
.hdr-hearts.empty{ background:color-mix(in srgb, var(--danger) 22%, var(--surface-2)); }

/* Primary button — accent fill, pressable depth, display type */
.btn{
  background:var(--accent-1); color:#fff; border:0; border-radius:14px;
  padding:13px 22px; font-weight:700; font-size:15px; letter-spacing:.01em;
  text-transform:none; font-family:var(--font-display);
  box-shadow:0 3px 0 color-mix(in srgb, var(--accent-1) 58%, #000), var(--shadow-sm);
  transition:filter var(--dur-fast), transform .07s, box-shadow .07s;
}
.btn:hover{ filter:brightness(1.07); }
.btn:active{ transform:translateY(3px); box-shadow:0 0 0 0 transparent; }
.btn.secondary{
  background:var(--surface); color:var(--text);
  border:1px solid var(--border); box-shadow:0 3px 0 var(--border);
  text-transform:none;
}
.btn.secondary:active{ transform:translateY(3px); box-shadow:0 0 0 0 var(--border); }
.btn.ghost{
  background:transparent; color:var(--text-dim); box-shadow:none;
  border:0; text-transform:none; font-weight:700;
}
.btn.ghost:active{ transform:none; }
.btn.cta-green{ background:var(--success); box-shadow:0 3px 0 color-mix(in srgb, var(--success) 58%, #000), var(--shadow-sm); }
.btn:disabled{ filter:grayscale(.5) opacity(.6); box-shadow:0 3px 0 var(--border); }

/* Big primary CTA — the one accent-saturated element on Home */
.today-cta{
  background:var(--accent-1); color:#fff; border:0; border-radius:var(--radius-lg);
  box-shadow:0 4px 0 color-mix(in srgb, var(--accent-1) 58%, #000), 0 16px 40px -12px var(--accent-glow);
  padding:20px 24px;
}
.today-cta:hover{ filter:brightness(1.06); transform:none; }
.today-cta:active{ transform:translateY(4px); box-shadow:0 0 0 0 transparent; }
.today-cta .tc-main{ font-weight:700; font-family:var(--font-display); text-transform:none; letter-spacing:-.01em; }
.today-cta:disabled{ background:var(--surface-2); color:var(--text-dim); box-shadow:0 4px 0 var(--border); }

/* Cards — soft elevation, hairline borders */
.sp,.quests-card,.league-card,.shop-card,.ach-card,.path-wrap,.drill-card,
.quiz-controls,.drill-controls,.lesson-card,.shop-item,.ach-cell,
.score-row,.more-stats,.pcode{
  border:1px solid var(--border); border-radius:var(--radius);
  box-shadow:var(--shadow-sm);
}
.drill-card,.lesson-card{ box-shadow:var(--shadow); }
.callout{ border:1px solid var(--border); border-left-width:4px; border-radius:var(--radius-sm); box-shadow:none; }

/* Answer options — glass rows with press depth */
.q-option{
  border:1px solid var(--border); border-radius:14px; background:var(--surface);
  box-shadow:var(--shadow-sm); font-weight:600; padding:14px 16px;
  transition:transform .06s, box-shadow .06s, border-color .12s, background .12s;
}
.q-option:not(.disabled):hover{ background:var(--surface-2); border-color:var(--accent-line); }
.q-option:not(.disabled):active{ transform:translateY(2px); box-shadow:none; }
.q-option.selected{ border-color:var(--accent-1); background:color-mix(in srgb, var(--accent-1) 8%, var(--surface)); box-shadow:0 0 0 1px var(--accent-1), var(--shadow-sm); }
.q-option.selected .marker{ background:var(--accent-1); color:#fff; }
.q-option.correct{ border-color:var(--success); background:var(--du-right-bg); box-shadow:0 0 0 1px var(--success), 0 0 20px -6px color-mix(in srgb, var(--success) 50%, transparent); }
.q-option.incorrect{ border-color:var(--danger); background:var(--du-wrong-bg); box-shadow:0 0 0 1px var(--danger); }
.q-option.correct .marker{ background:var(--success); }
.q-option.incorrect .marker{ background:var(--danger); }
.q-option .marker{ font-family:var(--font-dot); }

/* Progress bars — slim accent lines with glow */
.goal-bar-track,.qpb,.lp-seg{ height:10px !important; border-radius:999px; background:var(--surface-2); overflow:hidden; }
.xp-bar{ height:3px !important; border-radius:0; background:transparent; }
.goal-bar-fill,.xp-bar-fill,.qpb > i,.lp-seg .lp-in{
  background:var(--accent-1) !important;
  box-shadow:0 0 10px var(--accent-glow); border-radius:999px;
}
.lp-seg.cur .lp-in{ background:var(--accent-2) !important; }
.lp-seg.done .lp-in{ background:var(--accent-1) !important; }

/* THE PATH — horizontal scrolling track (minimal vertical footprint) */
.path{ max-width:none; margin:0; display:block; }
.path-wrap{ padding:14px 0 14px; overflow:hidden; }
.path-wrap .path-title{ padding:0 14px; }
.ch-band-body{ display:block; padding:0; align-items:initial; }
.path-track{
  display:flex; align-items:flex-start; gap:0; overflow-x:auto; overflow-y:hidden;
  width:100%; box-sizing:border-box;
  padding:42px 14px 14px; scroll-behavior:smooth; -webkit-overflow-scrolling:touch;
  scrollbar-width:thin;
}
/* gentle board-game zigzag */
.path-cell.pz-up{ transform:translateY(-9px); }
.path-cell.pz-dn{ transform:translateY(9px); }
.path-track::-webkit-scrollbar{ height:7px; }
.path-track::-webkit-scrollbar-thumb{ background:var(--border); border-radius:4px; }
.path-cell{ flex:0 0 auto; display:flex; flex-direction:column; align-items:center; position:relative; width:78px; }
.path-cell .path-mascot{ position:absolute; top:-30px; left:50%; transform:translateX(-50%); font-size:24px; line-height:1; animation:mascotBob 1.5s ease-in-out infinite; pointer-events:none; }
.path-cell .mini-trophy{ position:absolute; top:-7px; right:14px; font-size:15px; line-height:1; filter:drop-shadow(0 1px 0 rgba(0,0,0,.25)); }
.path-cap{ font-size:10px; font-weight:700; font-family:var(--font-dot); text-transform:uppercase; letter-spacing:.05em; color:var(--text-dim); max-width:74px; text-align:center; margin-top:7px; line-height:1.3; }
.path-cell.cur .path-cap{ color:var(--accent-1); }
.path-node{ width:52px; height:52px; border:0; }
.path-node .pn-face{ width:52px; height:52px; font-size:20px; font-weight:800; color:#fff; }
.path-node.done{ background:var(--success); box-shadow:0 4px 0 0 color-mix(in srgb, var(--success) 58%, #000); }
.path-node.current{ background:var(--accent-1); box-shadow:0 4px 0 0 color-mix(in srgb, var(--accent-1) 58%, #000), 0 0 22px -4px var(--accent-glow); }
.path-node.locked{ background:var(--surface-2); box-shadow:0 4px 0 0 var(--border); color:var(--text-dim); }
.path-node.legendary{ background:linear-gradient(135deg, var(--gold), #ff9f0a); box-shadow:0 4px 0 0 color-mix(in srgb, var(--gold) 55%, #000), 0 0 22px -4px color-mix(in srgb, var(--gold) 55%, transparent); }
.path-node:not(.locked):active{ transform:translateY(4px); box-shadow:0 0 0 0 #000; }
.path-node.done:hover,.path-node.current:hover{ transform:translateY(-2px); filter:brightness(1.06); }
.path-hconn{ flex:0 0 30px; height:4px; background:var(--border); border-radius:3px; align-self:flex-start; margin-top:55px; }
.path-hconn.hc-down{ transform:rotate(15deg); }
.path-hconn.hc-up{ transform:rotate(-15deg); }
.path-hconn.done{ background:var(--success); }
@media (prefers-reduced-motion: reduce){ .path-cell .path-mascot{ animation:none; } }

/* Pills / badges / chips */
.score-pill,.ach-tier,.lg-timer{ font-weight:800; }
.gem-bal{ background:var(--info); box-shadow:0 2px 0 color-mix(in srgb, var(--info) 58%, #000); }
.combo-pill{ background:var(--warn); box-shadow:0 4px 0 color-mix(in srgb, var(--warn) 58%, #000); font-weight:900; }
.chest-btn:not(:disabled){ filter:drop-shadow(0 4px 0 color-mix(in srgb, var(--gold) 55%, #000)); }
.ach-cell.got{ border-color:var(--gold); }
.lg-row.me{ background:color-mix(in srgb, var(--accent-2) 12%, transparent); border-radius:12px; }

/* Inputs */
input,select{ border:1px solid var(--border) !important; border-radius:12px !important; font-weight:600; background:var(--surface); color:var(--text); }
input:focus,select:focus{ border-color:var(--accent-1) !important; outline:none; box-shadow:0 0 0 3px var(--accent-glow); }
"""
s = s[:start] + new + s[end:]
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("skin replaced:", len(old), "->", len(new))
