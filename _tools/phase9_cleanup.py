# Phase 9: remove hearts UI/penalty, SRS box-spread + more-stats, badges/achievements,
# "Recommended for you"; group the learning-path dropdown by week via an injected WEEK_MAP.
import io

p = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
s = io.open(p, encoding="utf-8").read()

def rep(old, new, what):
    global s
    assert old in s, "MISSING: " + what
    assert s.count(old) == 1, "AMBIG: " + what
    s = s.replace(old, new)

# 1. header: remove hearts chip
rep("""    <span class="vital-chip hp-vc hdr-hearts" id="hearts-chip" title="Hearts — spent on wrong Quiz/Checkpoint">
      <span class="hh-i">❤️</span><span class="v-label">HP</span><span class="v-num" id="hearts-count">5</span>
    </span>
""", "", "hearts chip")

# 2. neuter the hearts SYSTEM (functions stay defined; callers keep working, just no-op)
rep("""// Gate the START of a Quiz / Checkpoint when out of hearts. Returns true if blocked.
function heartsBlock(onPractice) {
  if (heartsAvailable()) return false;""",
    """// Hearts system removed by user preference — never blocks, never penalizes.
function heartsBlock(onPractice) { return false; }
function _heartsBlock_legacy(onPractice) {
  if (heartsAvailable()) return false;""", "heartsBlock neuter")
rep("""function spendHeartOnWrong(x, y) {
  const before = state.hearts.count;
  const after = loseHeart();
  if (after < before) { heartLossFx(x, y); try { sfx.wrong(); } catch(e){} }
  renderHearts();""",
    """function spendHeartOnWrong(x, y) { return; }  // hearts system removed (user pref)
function _spendHeartOnWrong_legacy(x, y) {
  const before = state.hearts.count;
  const after = loseHeart();
  if (after < before) { heartLossFx(x, y); try { sfx.wrong(); } catch(e){} }
  renderHearts();""", "spendHeart neuter")

# 3. remove "Recommended for you"
rep("""  <!-- B3: Smart "What Next" recommendations (3 cards, refresh button) -->
  <div class="recs-wrap" id="recs-wrap">
    <div class="recs-head"><span>🎯 Recommended for you</span><button id="recs-refresh" class="recs-refresh" type="button" title="Re-roll">↻</button></div>
    <div class="recs-list" id="recs-list"></div>
  </div>

""", "", "recs markup")

# 4. remove goal bar + box legend + SRS box-spread / more-stats details
rep("""  <div class="goal-bar-track" style="margin:0 2px 4px;"><div class="goal-bar-fill" id="goal-bar"></div></div>
  <div class="box-legend" id="goal-msg" style="margin-bottom:14px;font-size:12px;">box 1 → 5 · red = needs work, gold = mastered</div>
  <details class="more-stats" style="margin-bottom:18px;"><summary>📊 SRS box spread &amp; goal</summary>
    <div class="ms-body">
      <div class="stat-strip" style="margin:6px 0 8px;">
        <div class="sp"><div class="sp-n"><span id="goal-done">0</span><span class="sp-d">/<span id="goal-target">20</span></span></div><div class="sp-l">🎯 Goal today</div></div>
      </div>
      <div class="box-bar" id="box-bar"></div>
    </div>
  </details>

""", "", "more-stats block")

# 5. badges/achievements: drop the Level tile's panel link + the ach-card panel
rep('    <div class="home-tile" data-panel="ach-card" title="Achievements"><div class="ht-n">⭐<span id="hp-level">1</span></div><div class="ht-l">🏅 Level</div></div>',
    '    <div class="home-tile flat"><div class="ht-n">⭐<span id="hp-level">1</span></div><div class="ht-l">Level</div></div>', "level tile flat")
rep("""  <!-- v2 P2 panels — hidden by default, opened from the home tiles via openPanel() -->
  <div id="panel-stash" style="display:none;">
    <div class="ach-card" id="ach-card">
      <h3>🏅 Achievements <span class="ach-prog" id="ach-prog"></span></h3>
      <div class="ach-grid" id="ach-grid"></div>
    </div>
  </div>

""", "", "ach panel")

# 6. WEEK_MAP sentinel — injected per-course post-build (build_weekmap.py). Placed right
#    before renderLessonPath so it's defined when the path renders.
rep("function renderLessonPath() {\n  const wrap = document.getElementById(\"lesson-path\");\n  if (!wrap) return;\n  const firstUnread = STUDY.findIndex(s => !state.read.includes(s.id));\n  const currentIdx = firstUnread === -1 ? STUDY.length - 1 : firstUnread;\n\n  if (!IS_COURSE) {",
    """const WEEK_MAP = /*WEEK_MAP*/null/*/WEEK_MAP*/;   // topic -> {w, label}, injected per course
function _weekOf(ch) { return (WEEK_MAP && WEEK_MAP[ch]) ? WEEK_MAP[ch] : null; }
function renderLessonPath() {
  const wrap = document.getElementById("lesson-path");
  if (!wrap) return;
  const firstUnread = STUDY.findIndex(s => !state.read.includes(s.id));
  const currentIdx = firstUnread === -1 ? STUDY.length - 1 : firstUnread;

  if (!IS_COURSE) {""", "WEEK_MAP const")

# 7. week-grouped dropdown — replace the flat <option> list with <optgroup> per week
rep("""    <select class="path-chapter-sel" id="ch-jump" aria-label="Chapter / exam guide">
      ${chapters.map(ch => {
        const inCh = byCh[ch];
        const dn = inCh.filter(i => state.read.includes(STUDY[i].id)).length;
        const tot = inCh.length;
        const mark = dn === tot && tot ? "✓ " : "";
        return `<option value="${escapeHtml(ch)}" ${ch === curCh ? "selected" : ""}>${mark}${escapeHtml(ch)} · ${dn}/${tot}</option>`;
      }).join("")}
    </select>""",
    """    <select class="path-chapter-sel" id="ch-jump" aria-label="Week / topic">
      ${_chapterOptionsByWeek(chapters, byCh, curCh)}
    </select>""", "week dropdown")

# 8. helper that builds the grouped options (added just above renderLessonPath block via the const we injected)
rep("const WEEK_MAP = /*WEEK_MAP*/null/*/WEEK_MAP*/;   // topic -> {w, label}, injected per course\nfunction _weekOf(ch) { return (WEEK_MAP && WEEK_MAP[ch]) ? WEEK_MAP[ch] : null; }",
    """const WEEK_MAP = /*WEEK_MAP*/null/*/WEEK_MAP*/;   // topic -> {w, label}, injected per course
function _weekOf(ch) { return (WEEK_MAP && WEEK_MAP[ch]) ? WEEK_MAP[ch] : null; }
// Group the path's chapter list into <optgroup>s by week so it's not one long list.
// Topics without a week fall under "Other"; with no WEEK_MAP at all it's a flat list.
function _chapterOptionsByWeek(chapters, byCh, curCh) {
  const opt = (ch) => {
    const inCh = byCh[ch];
    const dn = inCh.filter(i => state.read.includes(STUDY[i].id)).length;
    const tot = inCh.length;
    const mark = dn === tot && tot ? "✓ " : "";
    return `<option value="${escapeHtml(ch)}" ${ch === curCh ? "selected" : ""}>${mark}${escapeHtml(chDisp ? ch : ch)} · ${dn}/${tot}</option>`;
  };
  if (!WEEK_MAP || !Object.keys(WEEK_MAP).length) return chapters.map(opt).join("");
  const groups = new Map();   // label -> {w, chs:[]}
  const other = [];
  chapters.forEach(ch => {
    const wk = _weekOf(ch);
    if (wk) { if (!groups.has(wk.label)) groups.set(wk.label, { w: wk.w, chs: [] }); groups.get(wk.label).chs.push(ch); }
    else other.push(ch);
  });
  const ordered = Array.from(groups.entries()).sort((a, b) => a[1].w - b[1].w);
  let html = ordered.map(([label, g]) => {
    const dn = g.chs.reduce((n, ch) => n + byCh[ch].filter(i => state.read.includes(STUDY[i].id)).length, 0);
    const tot = g.chs.reduce((n, ch) => n + byCh[ch].length, 0);
    return `<optgroup label="${escapeAttr(label)} · ${dn}/${tot}">${g.chs.map(opt).join("")}</optgroup>`;
  }).join("");
  if (other.length) html += `<optgroup label="Other">${other.map(opt).join("")}</optgroup>`;
  return html;
}""", "week options helper")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("phase9 applied")
