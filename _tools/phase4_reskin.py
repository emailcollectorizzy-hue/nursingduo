# Phase 4: Home/Review/Quiz/Stats/focus-shell PULSE reskin (CSS + tiny JS hook).
import io

p = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

def rep(old, new, what):
    global s
    assert old in s, "MISSING: " + what
    s = s.replace(old, new)

# 1. focus shell: full-bleed bg + glass top bar + slim glowing progress + accent submit
rep("""  display: none; flex-direction: column;
  background: var(--surface); color: var(--text);
  height: 100dvh;""",
    """  display: none; flex-direction: column;
  background: var(--bg); color: var(--text);
  height: 100dvh;""", "focus-shell bg")
rep('.focus-top { height: calc(40px + env(safe-area-inset-top, 0px)); padding-top: env(safe-area-inset-top, 0px); box-sizing: border-box; flex-shrink: 0; display: flex; align-items: center; padding-left: 12px; padding-right: 12px; gap: 10px; border-bottom: 1px solid var(--border); background: var(--surface); }',
    '.focus-top { height: calc(44px + env(safe-area-inset-top, 0px)); padding-top: env(safe-area-inset-top, 0px); box-sizing: border-box; flex-shrink: 0; display: flex; align-items: center; padding-left: 12px; padding-right: 12px; gap: 10px; border-bottom: 1px solid var(--border); background: var(--glass); -webkit-backdrop-filter: blur(18px) saturate(1.4); backdrop-filter: blur(18px) saturate(1.4); }', "focus-top glass")
rep('.focus-top .focus-progress { flex: 1; height: 12px; background: var(--surface-2); border-radius: 999px; overflow: hidden; border: 1px solid var(--border); }',
    '.focus-top .focus-progress { flex: 1; height: 6px; background: var(--surface-2); border-radius: 999px; overflow: hidden; }', "focus-progress")
rep('.focus-top .focus-progress > div { height: 100%; background: linear-gradient(90deg, var(--accent-2), var(--accent-1, var(--accent-2))); border-radius: 999px; transition: width .35s cubic-bezier(.2,.7,.3,1); }',
    '.focus-top .focus-progress > div { height: 100%; background: var(--accent-1); box-shadow: 0 0 10px var(--accent-glow); border-radius: 999px; transition: width .35s var(--ease-out); }', "focus-progress fill")
rep('.focus-top .focus-counter { font-size: 12px; color: var(--text-dim); font-weight: 700; min-width: 44px; text-align: right; }',
    '.focus-top .focus-counter { font-family: var(--font-dot); font-size: 12px; color: var(--text-dim); font-weight: 700; min-width: 44px; text-align: right; letter-spacing: .06em; }', "focus-counter doto")
rep('.focus-action .focus-submit { background: var(--accent-2); color: #fff; border: 0; border-radius: 12px; padding: 13px 26px; font-weight: 800; font-size: 15px; cursor: pointer; box-shadow: 0 3px 0 color-mix(in srgb, var(--accent-2) 55%, #000); transition: transform .1s, box-shadow .1s; }',
    '.focus-action .focus-submit { background: var(--accent-1); color: #fff; border: 0; border-radius: 12px; padding: 13px 26px; font-weight: 700; font-family: var(--font-display); font-size: 15px; cursor: pointer; box-shadow: 0 3px 0 color-mix(in srgb, var(--accent-1) 58%, #000); transition: transform .1s, box-shadow .1s; }', "focus-submit")

# 2. mock-exam CTA: gradient → flat danger-tint card
rep('.mock-exam-cta { display: flex; align-items: center; gap: 14px; width: 100%; padding: 14px 18px; margin: 0 0 14px; background: linear-gradient(135deg, #ef4444, #f97316); color: #fff; border: 0; border-radius: var(--radius); cursor: pointer; box-shadow: 0 4px 0 #b91c1c; font: inherit; text-align: left; transition: transform .12s, box-shadow .12s; }',
    '.mock-exam-cta { display: flex; align-items: center; gap: 14px; width: 100%; padding: 14px 18px; margin: 0 0 14px; background: color-mix(in srgb, var(--danger) 9%, var(--surface)); color: var(--text); border: 1px solid color-mix(in srgb, var(--danger) 35%, var(--border)); border-radius: var(--radius); cursor: pointer; box-shadow: var(--shadow-sm); font: inherit; text-align: left; transition: transform .12s, box-shadow .12s, border-color .12s; }', "mock-exam cta")
rep('.mock-exam-cta:hover { transform: translateY(-1px); }',
    '.mock-exam-cta:hover { transform: translateY(-1px); border-color: var(--danger); box-shadow: 0 8px 24px -8px color-mix(in srgb, var(--danger) 40%, transparent); }', "mock-exam hover")
rep('.mock-exam-cta:active { transform: translateY(2px); box-shadow: 0 2px 0 #b91c1c; }',
    '.mock-exam-cta:active { transform: translateY(1px); }', "mock-exam active")
rep('.mock-exam-cta .me-title { font-size: 17px; font-weight: 800; letter-spacing: -.01em; }',
    '.mock-exam-cta .me-title { font-size: 17px; font-weight: 700; letter-spacing: -.01em; font-family: var(--font-display); color: var(--danger); }', "mock-exam title")
rep('.mock-exam-cta .me-sub { font-size: 12.5px; opacity: .92; margin-top: 2px; }',
    '.mock-exam-cta .me-sub { font-size: 12.5px; color: var(--text-dim); margin-top: 2px; }', "mock-exam sub")

# 3. results hero: gradient → surface card with accent glow + Doto score
rep('.results-hero { text-align: center; padding: 36px 24px; background: linear-gradient(135deg, var(--accent-1), var(--accent-2)); color: white; border-radius: var(--radius); margin-bottom: 20px; }',
    '.results-hero { text-align: center; padding: 36px 24px; background: var(--surface); color: var(--text); border: 1px solid var(--accent-line); border-radius: var(--radius-lg); margin-bottom: 20px; box-shadow: var(--shadow), 0 0 48px -18px var(--accent-glow); position: relative; overflow: hidden; }\n.results-hero::before { content: ""; position: absolute; inset: -40% -20%; background: radial-gradient(50% 50% at 50% 20%, var(--accent-soft), transparent 70%); pointer-events: none; }', "results hero")
rep('.results-hero .score { font-size: 64px; font-weight: 800; margin: 8px 0; letter-spacing: -0.03em; }',
    '.results-hero .score { font-family: var(--font-dot); font-size: 72px; font-weight: 700; margin: 8px 0; letter-spacing: -0.01em; color: var(--accent-1); position: relative; }', "results score doto")

# 4. legacy home-hero gradient → accent-soft card (still referenced by review/quiz panels)
rep(""".home-hero {
  background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
  color: white;
  padding: 32px;
  border-radius: var(--radius);
  margin-bottom: 24px;
  box-shadow: var(--shadow);
}""",
    """.home-hero {
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
  padding: 32px;
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
  box-shadow: var(--shadow);
}""", "home-hero")

# 5. exam chip → monitor chip
rep('.exam-chip { display: inline-block; background: rgba(255,255,255,0.18); backdrop-filter: blur(4px); color: white; padding: 5px 14px; border-radius: 999px; font-size: 13px; font-weight: 600; margin-top: 10px; }',
    '.exam-chip { display: inline-block; background: var(--surface-2); border: 1px solid var(--accent-line); color: var(--text); padding: 5px 14px; border-radius: 999px; font-family: var(--font-dot); font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; margin-top: 10px; }', "exam chip")

# 6. study/lesson tables: gradient header → flat surface header with accent ink
for sel, white in (("study-section", "white"), ("lesson-card", "#fff")):
    old_th = ".SEL th { background: linear-gradient(135deg, var(--accent-1), var(--accent-2)); color: WHITE; padding: 11px 13px; text-align: left; font-weight: 800; border: 1px solid color-mix(in srgb, var(--accent-1) 60%, #000); }".replace("SEL", sel).replace("WHITE", white)
    new_th = ".SEL th { background: var(--surface-2); color: var(--accent-1); padding: 11px 13px; text-align: left; font-weight: 800; font-family: var(--font-display); border: 1px solid var(--border); border-bottom: 2px solid var(--accent-line); }".replace("SEL", sel)
    rep(old_th, new_th, sel + " th")

# 7. repeat tap button: gradient → accent
rep('.repeat-tap-btn { background: linear-gradient(135deg, var(--accent-1), var(--accent-2)); color: white; border: none; padding: 15px 40px; border-radius: 999px; font-size: 18px; font-weight: 700; cursor: pointer; transition: transform 0.1s, box-shadow 0.15s; box-shadow: 0 4px 18px rgba(0,0,0,0.18); letter-spacing: 0.01em; user-select: none; }',
    '.repeat-tap-btn { background: var(--accent-1); color: white; border: none; padding: 15px 40px; border-radius: 999px; font-size: 18px; font-weight: 700; font-family: var(--font-display); cursor: pointer; transition: transform 0.1s, box-shadow 0.15s; box-shadow: 0 4px 0 color-mix(in srgb, var(--accent-1) 58%, #000), 0 10px 26px -10px var(--accent-glow); letter-spacing: 0.01em; user-select: none; }', "repeat tap btn")

# 8. progress fill bars that kept the old gradient
rep('.progress-fill { height: 100%; background: linear-gradient(90deg, var(--accent-1), var(--accent-2)); transition: width 0.4s; border-radius: 999px; }',
    '.progress-fill { height: 100%; background: var(--accent-1); box-shadow: 0 0 8px var(--accent-glow); transition: width 0.4s; border-radius: 999px; }', "progress fill")
rep(".session-prog .fill { height:100%; background: linear-gradient(90deg,var(--accent-1),var(--accent-2)); width:0; transition: width .4s ease; }",
    ".session-prog .fill { height:100%; background: var(--accent-1); box-shadow: 0 0 10px var(--accent-glow); width:0; transition: width .4s ease; }", "session prog")

# 9. Doto numerals across dashboards
doto_css = """
/* PULSE: dot-matrix numerals on every headline metric */
.readiness-card .readiness-num, .me-score-num, .review-due-num, .sp-n, .home-tile .ht-n,
.ms-k, .stats-summary .ss-num, .sd-stat .n, .results-stat .num, .topic-tile .tt-pct,
.ring-label, .quest-n, .lg-row .lg-xp { font-family: var(--font-dot) !important; letter-spacing: .02em; }
.review-due-num { font-size: 64px; line-height: 1; }
.review-head { position: relative; }
.review-head::before { content: "DUE NOW"; position: absolute; top: 10px; left: 22px; font-family: var(--font-dot); font-size: 10px; font-weight: 700; letter-spacing: .2em; color: var(--text-dim); }
"""
anchor = "@media (prefers-reduced-motion: reduce){\n  .fc-fling-right,.fc-fling-left,.fc-fling-up,.fc-deal{ animation:none; }\n  .fc-under{ display:none; }\n}\n"
rep(anchor, anchor + doto_css, "doto numerals block")

# 10. switchTab: stagger-reveal direct children of the freshly opened tab (not study)
rep("""  if (name === "quiz") renderCases();
  window.scrollTo(0, 0);
}""",
    """  if (name === "quiz") renderCases();
  window.scrollTo(0, 0);
  // PULSE: stagger-reveal the freshly opened tab's top-level blocks (study runs its own choreography)
  if (name !== "study") {
    const panel = document.getElementById("tab-" + name);
    if (panel) {
      Array.from(panel.children).slice(0, 14).forEach(el => { el.setAttribute("data-rv", ""); el.classList.remove("rv-in"); });
      PM.reveal(panel);
    }
  }
}""", "switchTab reveal hook")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("phase4 applied, delta:", len(s) - n0)
