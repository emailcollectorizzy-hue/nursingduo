// E2E: cards deck — reveal, grade via keyboard, fling, lap repeat, SRS write, filmstrip.
import { chromium } from "playwright";
import { pathToFileURL } from "url";

const [file, outdir] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1024, height: 768 } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto(pathToFileURL(file).href);
await page.evaluate(() => { localStorage.clear(); });
await page.reload();
await page.waitForTimeout(400);
await page.evaluate(() => { localStorage.setItem("quizpage:tour-done", "1"); });
await page.reload();
await page.waitForTimeout(400);
await page.evaluate(() => { state.dark = true; state.darkSet = true; applyTheme(); switchTab("cards"); });
await page.waitForTimeout(400);

const stage = await page.evaluate(() => ({
  unders: document.querySelectorAll(".fc-under").length,
  card: !!document.querySelector(".fc-stage .drill-card"),
}));
await page.screenshot({ path: `${outdir}/cards-deck.png` });

// card 1: reveal → "Knew it" (J)
await page.click("#fc-reveal-btn");
await page.waitForTimeout(400);
await page.screenshot({ path: `${outdir}/cards-revealed.png` });
await page.keyboard.press("j");
await page.waitForTimeout(300);
await page.screenshot({ path: `${outdir}/cards-graded.png` });
await page.keyboard.press(" ");
await page.waitForTimeout(700);

// card 2: reveal → "Don't know" (M) → lap should be queued
await page.click("#fc-reveal-btn");
await page.waitForTimeout(300);
await page.keyboard.press("m");
await page.waitForTimeout(300);
await page.keyboard.press(" ");
await page.waitForTimeout(700);
await page.screenshot({ path: `${outdir}/cards-after2.png` });

const after = await page.evaluate(() => ({
  srsCount: Object.keys(state.srs).filter((k) => k.startsWith("fc:")).length,
  boxes: Object.entries(state.srs).filter(([k]) => k.startsWith("fc:")).map(([, v]) => v.box),
  laps: cardsState.laps.length,
  history: (cardsState.history || []).map((h) => h.outcome),
  strip: document.querySelectorAll(".fc-hist").length,
  progLabel: document.getElementById("cards-prog-label")?.textContent,
}));
console.log(JSON.stringify({ stage, after, errors: errors.slice(0, 5) }, null, 1));
await browser.close();
