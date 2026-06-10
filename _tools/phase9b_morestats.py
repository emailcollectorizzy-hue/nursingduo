# Phase 9b: remove the "More stats & badges" panel + the now-dead renderHome writes
# that targeted removed elements (ring-due, box-bar, goal-*, read-*, dash-best-streak,
# score-history, badges). due-count + dash-streak tiles, greeting, exam, activity,
# readiness all stay.
import io

p = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
s = io.open(p, encoding="utf-8").read()

def rep(old, new, what):
    global s
    assert old in s, "MISSING: " + what
    assert s.count(old) == 1, "AMBIG: " + what
    s = s.replace(old, new)

# 1. remove the More stats & badges panel markup
rep("""  <details class="more-stats">
    <summary>📊 More stats &amp; badges</summary>
    <div class="ms-body">
      <div class="ms-row">
        <div class="ms-cell"><div class="ms-k"><span id="read-pct">0</span>%</div><div class="ms-l">📖 Read · <span id="read-count">0</span>/<span id="read-total">0</span></div><svg style="display:none"><circle id="ring-read" r="32" stroke-dasharray="201" stroke-dashoffset="201"></circle><circle id="ring-due" r="32" stroke-dasharray="201" stroke-dashoffset="201"></circle></svg></div>
<div class="ms-cell"><div class="ms-k">🔥 <span id="dash-best-streak">0</span></div><div class="ms-l">Best streak</div></div>
      </div>
      <div style="margin-top:14px;"><div class="path-title" style="text-align:left;margin-bottom:8px;">🏆 Badges</div><div class="badge-row" id="badge-row"></div></div>
      <div style="margin-top:14px;"><div class="path-title" style="text-align:left;margin-bottom:8px;">📈 Recent quiz attempts</div><div class="score-history" id="score-history"><em style="color: var(--text-dim); font-size: 14px;">No attempts yet.</em></div></div>
    </div>
  </details>
""", "", "more-stats-badges panel")

# 2. renderHome: drop the due-ring + box-bar writes (keep due-count text)
rep("""  document.getElementById("due-count").textContent = due.length;
  document.getElementById("ring-due").setAttribute("stroke-dasharray", circ);
  document.getElementById("ring-due").setAttribute("stroke-dashoffset", circ - (circ * Math.min(100,duePct) / 100));
  const bc = boxCounts();
  document.getElementById("box-bar").innerHTML = [1,2,3,4,5].map(b =>
    `<div class="box-seg box-${b}" style="flex:${Math.max(bc[b],0.001)}" title="Box ${b}: ${bc[b]}">${bc[b]||""}</div>`).join("");
  const tcMain""",
    """  { const dc = document.getElementById("due-count"); if (dc) dc.textContent = due.length; }
  const tcMain""", "due-ring/box-bar writes")

# 3. drop the daily-goal block (markup removed in phase9)
rep("""  // Daily goal
  const gd = goalToday(), gt = state.dailyGoal;
  document.getElementById("goal-done").textContent = gd;
  document.getElementById("goal-target").textContent = gt;
  const gbar = document.getElementById("goal-bar");
  const gpct = Math.min(100, Math.round(gd/gt*100));
  gbar.style.width = gpct + "%";
  const gmsg = document.getElementById("goal-msg");
  if (gd >= gt) { gmsg.textContent = "🎉 Goal hit — nice work!"; gbar.classList.remove("goal-hit"); void gbar.offsetWidth; gbar.classList.add("goal-hit"); }
  else gmsg.textContent = `${gt-gd} more to hit today's goal`;

  // Reading progress
  const readN = state.read.length, totalN = STUDY.length;
  const readPct = totalN ? Math.round((readN / totalN) * 100) : 0;
  document.getElementById("read-pct").textContent = readPct;
  document.getElementById("read-count").textContent = readN;
  document.getElementById("read-total").textContent = totalN;
  document.getElementById("ring-read").setAttribute("stroke-dasharray", circ);
  document.getElementById("ring-read").setAttribute("stroke-dashoffset", circ - (circ * readPct / 100));

  // Drill mastery ring (now reflects box 4-5 = real retention, not just tapped)
  const drillTotal = DRILLS.length;
  const drillMastered = DRILLS.filter(d => { const r = state.srs["d:"+drillKey(d)]; return r && r.box >= 4; }).length;
  const drillPct = drillTotal ? Math.round((drillMastered / drillTotal) * 100) : 0;
  document.getElementById("drill-pct").textContent = drillPct;
  document.getElementById("drill-count").textContent = drillMastered;
  document.getElementById("drill-total").textContent = drillTotal;
  document.getElementById("ring-drill").setAttribute("stroke-dasharray", circ);
  document.getElementById("ring-drill").setAttribute("stroke-dashoffset", circ - (circ * drillPct / 100));

  // Streak card → day streak (the habit metric)
  document.getElementById("dash-streak").textContent = state.dayStreak.count;
  document.getElementById("dash-best-streak").textContent = state.dayStreak.best;

  // Score history
  const hist = document.getElementById("score-history");
  if (!state.attempts.length) {
    hist.innerHTML = `<em style="color: var(--text-dim); font-size: 14px;">No attempts yet — head to the Quiz tab.</em>`;
  } else {
    hist.innerHTML = state.attempts.slice(-5).reverse().map(a => {
      const pct = Math.round((a.correct / a.total) * 100);
      const cls = pct >= 85 ? "good" : pct >= 70 ? "mid" : "low";
      const d = new Date(a.date);
      const dStr = d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) + " · " + d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
      return `<div class="score-row"><span>${dStr} · ${a.mode}</span><span style="color: var(--text-dim); font-size: 13px;">${a.correct}/${a.total}</span><span class="score-pill ${cls}">${pct}%</span></div>`;
    }).join("");
  }

  // Badges
  renderBadges();

  // Greeting""",
    """  // Streak tile → day streak (the habit metric)
  { const ds = document.getElementById("dash-streak"); if (ds) ds.textContent = state.dayStreak.count; }

  // Greeting""", "renderHome dead writes")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("phase9b applied")
