// E2E: recall gate → focus shell → grade all → unlock next chunk → checkpoint → finish.
import { chromium } from "playwright";
import { pathToFileURL } from "url";

const [file, outdir] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1024, height: 768 } });
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
await page.evaluate(() => {
  state.dark = true; state.darkSet = true; applyTheme();
  state.read = [STUDY[0].id]; saveState();
  switchTab("study"); goToSection(1); // first gated section
});
await page.waitForTimeout(400);

const before = await page.evaluate(() => ({
  locked: document.querySelectorAll(".ls-chunk.ls-locked").length,
  gateLabel: document.querySelector(".ls-gate-btn")?.textContent,
}));

// open the first gate
await page.click(".ls-gate-btn");
await page.waitForTimeout(400);
const inShell = await page.evaluate(() => document.body.classList.contains("in-lesson"));
await page.screenshot({ path: `${outdir}/gate-shell.png` });

// grade through the flash gate: flip (click card / reveal) then "Knew it" until shell closes
for (let i = 0; i < 30; i++) {
  const open = await page.evaluate(() => document.body.classList.contains("in-lesson"));
  if (!open) break;
  await page.evaluate(() => {
    const flip = document.querySelector(".fc-gate-flip, #fc-reveal-btn");
    if (flip && flip.offsetParent) { flip.click(); return; }
    const conf = document.querySelector('.fc-gate-confs .conf-btn[data-c="3"], #fc-conf-area .conf-btn[data-c="3"], .focus-body .conf-btn[data-c="3"]');
    if (conf) conf.click();
  });
  await page.waitForTimeout(250);
}
await page.waitForTimeout(600);
const after = await page.evaluate(() => ({
  inShell: document.body.classList.contains("in-lesson"),
  locked: document.querySelectorAll(".ls-chunk.ls-locked").length,
  gatesPassed: document.querySelectorAll(".ls-gate-done").length,
  scrollY: Math.round(window.scrollY),
  lessonStepState: (() => { const s = STUDY[currentSectionIdx]; return state.lessonStep[s.id]; })(),
  gateState: Object.keys(state.lessonGate || {}).length,
}));
await page.screenshot({ path: `${outdir}/gate-after.png` });
console.log(JSON.stringify({ before, inShell, after, errors: errors.slice(0, 5) }, null, 1));
await browser.close();
