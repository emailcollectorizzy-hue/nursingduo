// Scroll-behavior probe for the study scrollytelling.
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
await page.waitForTimeout(500);
await page.evaluate(() => { state.dark = true; state.darkSet = true; applyTheme(); switchTab("study"); });
await page.waitForTimeout(500);

// pick a section with a gate: walk sections until one has a .ls-gate-btn
const info = await page.evaluate(() => {
  const out = { sections: STUDY.length, gates: [] };
  for (let i = 0; i < Math.min(STUDY.length, 7); i++) {
    // peek: compute steps + cards without navigating
    const steps = splitSectionIntoSteps(STUDY[i].html, STUDY[i].title);
    assignQuickChecks(steps, STUDY[i].title);
    assignFlashcardsPerSubsection(steps, STUDY[i].title);
    out.gates.push(steps.filter((st) => (st.flashCards || []).length).length);
  }
  return out;
});
console.log("gate-map:", JSON.stringify(info));

// scroll mid-way: hero shrink + reveals
await page.evaluate(() => window.scrollTo(0, Math.round(window.innerHeight * 0.7)));
await page.waitForTimeout(700);
await page.screenshot({ path: `${outdir}/study-scrolled.png` });

// jump to a gated section (find first section with ≥2 gates)
const target = info.gates.findIndex((g) => g >= 2);
if (target > 0) {
  await page.evaluate((t) => { state.read = STUDY.slice(0, t).map((s) => s.id); saveState(); goToSection(t); }, target);
  await page.waitForTimeout(400);
}
const lockProbe = await page.evaluate(() => {
  const locked = document.querySelectorAll(".ls-chunk.ls-locked").length;
  const gates = document.querySelectorAll(".ls-gate-btn").length;
  const dots = document.querySelectorAll(".ls-dot").length;
  const lockedEl = document.querySelector(".ls-chunk.ls-locked");
  if (lockedEl) lockedEl.scrollIntoView({ block: "center" });
  return { locked, gates, dots, railCount: document.getElementById("ls-rail-count")?.textContent };
});
await page.waitForTimeout(600);
await page.screenshot({ path: `${outdir}/study-locked.png` });
console.log("lock-probe:", JSON.stringify(lockProbe), "errors:", JSON.stringify(errors.slice(0, 5)));
await browser.close();
