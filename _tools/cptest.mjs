// E2E: checkpoint in focus shell → finish section → next section unlocks; resume; reduced-motion.
import { chromium } from "playwright";
import { pathToFileURL } from "url";

const [file, outdir] = process.argv.slice(2);
const browser = await chromium.launch();

// ---------- main pass ----------
let page = await browser.newPage({ viewport: { width: 1024, height: 768 } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto(pathToFileURL(file).href);
await page.evaluate(() => {
  const k = Object.keys(localStorage).find((x) => x.startsWith("quizpage:"));
  const s = k ? JSON.parse(localStorage.getItem(k) || "{}") : {};
  s.tourSeen = true; s.tourDone = true;
  if (k) localStorage.setItem(k, JSON.stringify(s));
});
await page.reload();
await page.waitForTimeout(400);

// Section 0 (Introduction, ungated, 2 steps) → walk to checkpoint? It has no gates.
// Pass all gates of section 1 programmatically EXCEPT the checkpoint, then run checkpoint UI.
await page.evaluate(() => {
  state.dark = true; state.darkSet = true; applyTheme();
  switchTab("study"); goToSection(0);
});
await page.waitForTimeout(300);
const sec0 = await page.evaluate(() => ({
  unlocked1: sectionUnlocked(1),
  cpPresent: !!document.getElementById("lsn-cp-cta") || !!document.getElementById("lsn-finish"),
}));

// finish section 0 via the finish button (scroll there first)
await page.evaluate(() => { const f = document.getElementById("lsn-finish"); f?.scrollIntoView(); });
await page.waitForTimeout(200);
const hadCp = await page.evaluate(() => !!document.getElementById("lsn-cp-cta"));
if (hadCp) {
  await page.click("#lsn-cp-cta");
  await page.waitForTimeout(400);
  // answer checkpoint MCQs in focus shell: click first option then submit/continue
  for (let i = 0; i < 40; i++) {
    const open = await page.evaluate(() => document.body.classList.contains("in-lesson"));
    if (!open) break;
    await page.evaluate(() => {
      const opt = document.querySelector(".focus-option:not(.disabled)");
      if (opt) opt.click();
      const sub = document.querySelector(".focus-submit");
      if (sub && !sub.disabled) sub.click();
    });
    await page.waitForTimeout(200);
  }
}
await page.evaluate(() => document.getElementById("lsn-finish")?.click());
await page.waitForTimeout(500);
const done = await page.evaluate(() => ({
  sectionDone: !!document.querySelector(".section-done"),
  read0: state.read.includes(STUDY[0].id),
  unlocked1: sectionUnlocked(1),
}));
await page.screenshot({ path: `${outdir}/section-done.png` });

// resume check: set furthest step on section 1, reload, open study → should scroll to it
await page.evaluate(() => { goToSection(1); });
await page.waitForTimeout(300);
await page.evaluate(() => { const s = STUDY[1]; state.lessonStep[s.id] = 2; state.lessonGate[s.id + ":0"] = 1; state.lessonGate[s.id + ":1"] = 1; saveState(); });
await page.reload();
await page.waitForTimeout(500);
await page.evaluate(() => { switchTab("study"); });
await page.waitForTimeout(800);
const resume = await page.evaluate(() => ({ scrollY: Math.round(window.scrollY), lessonIdx, sec: currentSectionIdx }));
await browser.close();

// ---------- reduced-motion pass ----------
const browser2 = await chromium.launch();
const ctx2 = await browser2.newContext({ reducedMotion: "reduce", viewport: { width: 1024, height: 768 } });
page = await ctx2.newPage();
const errors2 = [];
page.on("pageerror", (e) => errors2.push(String(e)));
await page.goto(pathToFileURL(file).href);
await page.waitForTimeout(400);
await page.evaluate(() => {
  state.dark = true; state.darkSet = true; applyTheme(); switchTab("study");
});
await page.waitForTimeout(500);
const rm = await page.evaluate(() => ({
  pmReduced: PM.reduced,
  heroStatic: getComputedStyle(document.getElementById("ls-hero")).position,
  revealsVisible: Array.from(document.querySelectorAll("[data-rv]")).every((n) => getComputedStyle(n).opacity === "1"),
}));
await page.screenshot({ path: `${outdir}/study-reduced.png` });
await browser2.close();

console.log(JSON.stringify({ sec0, done, resume, rm, errors: errors.slice(0, 4), errors2: errors2.slice(0, 4) }, null, 1));
