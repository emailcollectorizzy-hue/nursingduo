// E2E: continuous flow — finish a section by scrolling, next section appends, no interstitial.
import { chromium } from "playwright";
import { pathToFileURL } from "url";

const [file, outdir] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1024, height: 768 } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto(pathToFileURL(file).href);
await page.evaluate(() => { localStorage.clear(); localStorage.setItem("quizpage:tour-done", "1"); });
await page.reload();
await page.waitForTimeout(900);

// Section 0 (Introduction-style, often no gates/checkpoint) → continuous into section 1
await page.evaluate(() => { switchTab("study"); });
await page.waitForTimeout(500);
const init = await page.evaluate(() => ({
  sec: currentSectionIdx,
  blocks: document.querySelectorAll(".ls-section").length,
  finale: !!document.querySelector(".ls-finale"),
  hasCp: (_lsSteps[0] || []).some((st) => st.kind === "checkpoint"),
  gates: lsLockFrom(0) < (_lsSteps[0] || []).length,
}));

// clear any gates in section 0 via inline recall (grade with J)
let guard = 0;
while (guard++ < 40) {
  const g = await page.evaluate(() => {
    if (!_lsActiveRecall) return null;
    const host = document.getElementById("ls-recall-" + _lsActiveRecall.secIdx + "-" + _lsActiveRecall.stepIdx);
    if (host) host.scrollIntoView({ block: "center" });
    return _lsActiveRecall.stepIdx;
  });
  if (g === null) break;
  await page.waitForTimeout(300);
  await page.keyboard.press(" ");
  await page.waitForTimeout(250);
  await page.keyboard.press("j");
  await page.waitForTimeout(500);
}

// scroll to the finale → should auto-complete + append section 1
await page.evaluate(() => { document.querySelector(".ls-finale").scrollIntoView({ block: "center" }); });
await page.waitForTimeout(1200);
// if checkpoint pending, skip it via the inline skip button
const skipped = await page.evaluate(() => {
  const sk = document.querySelector("[data-cpskip]");
  if (sk) { sk.click(); return true; }
  return false;
});
await page.waitForTimeout(1200);

const after = await page.evaluate(() => ({
  blocks: document.querySelectorAll(".ls-section").length,
  blockSecs: Array.from(document.querySelectorAll(".ls-section")).map((b) => b.dataset.sec),
  interstitial: !!document.querySelector(".section-done"),
  progressCodeShown: !!document.querySelector(".pc-code"),
  completeBanner: (document.querySelector(".ls-complete .eyebrow") || {}).textContent || null,
  read0: state.read.includes(STUDY[0].id),
  xp: state.xp,
  unlocked1: sectionUnlocked(1),
}));
await page.screenshot({ path: `${outdir}/flow-complete.png` });

// keep scrolling into section 1 — spy should switch currentSectionIdx + rail
await page.evaluate(() => { document.getElementById("ls-sec-1").scrollIntoView({ block: "start" }); });
await page.waitForTimeout(400);
await page.evaluate(() => { const c = document.querySelector('#ls-sec-1 .ls-chunk'); if (c) c.scrollIntoView({ block: "center" }); });
await page.waitForTimeout(800);
const inNext = await page.evaluate(() => ({
  sec: currentSectionIdx,
  railDots: document.querySelectorAll("#ls-rail-dots .ls-dot").length,
  counter: document.getElementById("sec-counter")?.textContent,
  lastSection: state.lastSection,
}));
await page.screenshot({ path: `${outdir}/flow-next-section.png` });
console.log(JSON.stringify({ init, skipped, after, inNext, errors: errors.slice(0, 6) }, null, 1));
await browser.close();
