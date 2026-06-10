# Phase 10: split the learning-path picker into two cascading dropdowns —
# Week selector → Topic selector (only the chosen week's topics). Falls back to a
# single topic dropdown when no WEEK_MAP (e.g. NS221).
import io

p = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
s = io.open(p, encoding="utf-8").read()

def rep(old, new, what):
    global s
    assert old in s, "MISSING: " + what
    assert s.count(old) == 1, "AMBIG: " + what
    s = s.replace(old, new)

# 1. replace _chapterOptionsByWeek with week-aware helpers
old_helper = '''// Group the path's chapter list into <optgroup>s by week so it's not one long list.
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
}'''
new_helper = '''// Group chapters into weeks (ordered) for the cascading Week → Topic pickers.
// Returns [{key, label, w, chs:[...]}], with an "Other" bucket last for unmapped
// topics. When there is no WEEK_MAP, returns a single synthetic group of all chapters.
function _pathWeekGroups(chapters) {
  if (!WEEK_MAP || !Object.keys(WEEK_MAP).length) {
    return [{ key: "__all__", label: "All topics", w: 0, chs: chapters.slice(), synthetic: true }];
  }
  const groups = new Map();   // label -> {w, chs}
  const other = [];
  chapters.forEach(ch => {
    const wk = _weekOf(ch);
    if (wk) { if (!groups.has(wk.label)) groups.set(wk.label, { w: wk.w, chs: [] }); groups.get(wk.label).chs.push(ch); }
    else other.push(ch);
  });
  const out = Array.from(groups.entries()).sort((a, b) => a[1].w - b[1].w)
    .map(([label, g]) => ({ key: label, label, w: g.w, chs: g.chs }));
  if (other.length) out.push({ key: "Other", label: "Other", w: 9999, chs: other });
  return out;
}
function _weekKeyOf(ch) { const wk = _weekOf(ch); return wk ? wk.label : "Other"; }
function _groupProgress(g, byCh) {
  const dn = g.chs.reduce((n, ch) => n + byCh[ch].filter(i => state.read.includes(STUDY[i].id)).length, 0);
  const tot = g.chs.reduce((n, ch) => n + byCh[ch].length, 0);
  return { dn, tot };
}'''
rep(old_helper, new_helper, "week helpers")

# 2. rewrite the course path bar + wiring for two cascading dropdowns
old_bar = '''  const bar = `<div class="path-chapter-bar">
    <button class="path-chapter-nav" id="path-prev-ch" type="button" title="Previous chapter" ${chPos <= 0 ? "disabled" : ""}>‹</button>
    <select class="path-chapter-sel" id="ch-jump" aria-label="Week / topic">
      ${_chapterOptionsByWeek(chapters, byCh, curCh)}
    </select>
    <button class="path-chapter-nav" id="path-next-ch" type="button" title="Next chapter" ${chPos >= chapters.length - 1 ? "disabled" : ""}>›</button>
  </div>
  <div class="path-chapter-progress">
    <div class="pcp-track"><div class="pcp-fill" style="width:${pctInCh}%"></div></div>
    <div class="pcp-label">${doneInCh}/${totalInCh} · ${pctInCh}%</div>
  </div>`;
  const track = _pathTrack(idxs, currentIdx);
  wrap.innerHTML = bar + track;
  _wirePathNodes(wrap);
  _scrollPathToCurrent(wrap);

  const sel = document.getElementById("ch-jump");
  if (sel) sel.addEventListener("change", () => {
    state.pathChapter = sel.value; saveState(); renderLessonPath();
  });
  function jump(delta) {
    const at = chapters.indexOf(curCh);
    const next = chapters[Math.max(0, Math.min(chapters.length - 1, at + delta))];
    if (next && next !== curCh) { state.pathChapter = next; saveState(); renderLessonPath(); }
  }
  document.getElementById("path-prev-ch")?.addEventListener("click", () => jump(-1));
  document.getElementById("path-next-ch")?.addEventListener("click", () => jump(+1));
}'''
new_bar = '''  // Two cascading pickers: Week → Topic. The Topic dropdown only lists the
  // chosen week's topics, so neither list is ever long.
  const weekGroups = _pathWeekGroups(chapters);
  const curWeekKey = _weekKeyOf(curCh);
  const curGroup = weekGroups.find(g => g.key === curWeekKey) || weekGroups[0];
  const hasWeeks = !(weekGroups.length === 1 && weekGroups[0].synthetic);

  const weekSelect = hasWeeks ? `<select class="path-week-sel" id="week-jump" aria-label="Week">
      ${weekGroups.map(g => { const pr = _groupProgress(g, byCh); const mk = pr.dn === pr.tot && pr.tot ? "✓ " : "";
        return `<option value="${escapeAttr(g.key)}" ${g.key === curGroup.key ? "selected" : ""}>${mk}${escapeHtml(g.label)} · ${pr.dn}/${pr.tot}</option>`; }).join("")}
    </select>` : "";

  const topicOpt = (ch) => {
    const inCh = byCh[ch];
    const dn = inCh.filter(i => state.read.includes(STUDY[i].id)).length;
    const tot = inCh.length;
    const mark = dn === tot && tot ? "✓ " : "";
    return `<option value="${escapeHtml(ch)}" ${ch === curCh ? "selected" : ""}>${mark}${escapeHtml(ch)} · ${dn}/${tot}</option>`;
  };
  const topicsInWeek = curGroup.chs;
  const tPos = topicsInWeek.indexOf(curCh);

  const bar = `${hasWeeks ? `<div class="path-week-bar">${weekSelect}</div>` : ""}
  <div class="path-chapter-bar">
    <button class="path-chapter-nav" id="path-prev-ch" type="button" title="Previous topic" ${tPos <= 0 ? "disabled" : ""}>‹</button>
    <select class="path-chapter-sel" id="ch-jump" aria-label="Topic">
      ${topicsInWeek.map(topicOpt).join("")}
    </select>
    <button class="path-chapter-nav" id="path-next-ch" type="button" title="Next topic" ${tPos >= topicsInWeek.length - 1 ? "disabled" : ""}>›</button>
  </div>
  <div class="path-chapter-progress">
    <div class="pcp-track"><div class="pcp-fill" style="width:${pctInCh}%"></div></div>
    <div class="pcp-label">${doneInCh}/${totalInCh} · ${pctInCh}%</div>
  </div>`;
  const track = _pathTrack(idxs, currentIdx);
  wrap.innerHTML = bar + track;
  _wirePathNodes(wrap);
  _scrollPathToCurrent(wrap);

  // Week change → jump to that week's first unread topic (or its first topic)
  const wsel = document.getElementById("week-jump");
  if (wsel) wsel.addEventListener("change", () => {
    const g = weekGroups.find(x => x.key === wsel.value);
    if (!g || !g.chs.length) return;
    const firstUnreadCh = g.chs.find(ch => byCh[ch].some(i => !state.read.includes(STUDY[i].id)));
    state.pathChapter = firstUnreadCh || g.chs[0];
    saveState(); renderLessonPath();
  });
  const sel = document.getElementById("ch-jump");
  if (sel) sel.addEventListener("change", () => {
    state.pathChapter = sel.value; saveState(); renderLessonPath();
  });
  // ‹ › step through THIS week's topics (keeps the two pickers in sync)
  function jump(delta) {
    const at = topicsInWeek.indexOf(curCh);
    const next = topicsInWeek[Math.max(0, Math.min(topicsInWeek.length - 1, at + delta))];
    if (next && next !== curCh) { state.pathChapter = next; saveState(); renderLessonPath(); }
  }
  document.getElementById("path-prev-ch")?.addEventListener("click", () => jump(-1));
  document.getElementById("path-next-ch")?.addEventListener("click", () => jump(+1));
}'''
rep(old_bar, new_bar, "two-dropdown bar")

# 3. CSS for the week bar
anchor = "/* C2 — course chapter-accordion path */"
css = '''/* Week selector — sits above the topic picker (two cascading dropdowns) */
.path-week-bar{ margin:0 0 8px; }
.path-week-sel{ width:100%; padding:11px 13px; border-radius:var(--radius-sm); border:1px solid var(--accent-line); background:color-mix(in srgb, var(--accent-1) 6%, var(--surface)); color:var(--text); font-family:var(--font-display); font-weight:700; font-size:14px; cursor:pointer; }
.path-week-sel:focus{ outline:none; border-color:var(--accent-1); box-shadow:0 0 0 3px var(--accent-glow); }
'''
rep(anchor, css + anchor, "week bar css")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("phase10 applied")
