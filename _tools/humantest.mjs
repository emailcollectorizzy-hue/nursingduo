// Simulate a human reading through the continuous flow: scroll, grade recalls, keep going.
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
await page.evaluate(() => { switchTab("study"); });
await page.waitForTimeout(500);

let snap = null;
for (let k = 0; k < 90; k++) {
  snap = await page.evaluate(() => {
    window.scrollBy({ top: Math.round(window.innerHeight * 0.55), behavior: "auto" });
    return {
      y: Math.round(window.scrollY),
      atBottom: window.scrollY + window.innerHeight >= document.body.scrollHeight - 6,
      recall: !!_lsActiveRecall && _lsRecallOnScreen(),
      blocks: document.querySelectorAll(".ls-section").length,
      sec: currentSectionIdx,
      readCount: state.read.length,
    };
  });
  await page.waitForTimeout(320);
  if (snap.recall) {
    for (let g = 0; g < 25; g++) {
      const more = await page.evaluate(() => !!_lsActiveRecall && _lsRecallOnScreen());
      if (!more) break;
      await page.keyboard.press(" ");
      await page.waitForTimeout(220);
      await page.keyboard.press("j");
      await page.waitForTimeout(460);
    }
  }
  // skip checkpoints inline if one is blocking the finale
  await page.evaluate(() => { const sk = document.querySelector("[data-cpskip]"); if (sk) { const r = sk.getBoundingClientRect(); if (r.top < window.innerHeight && r.bottom > 0) sk.click(); } });
  if (snap.readCount >= 2 && snap.sec >= 1) break;   // we've read 2 sections and are inside the 2nd+
}
const res = await page.evaluate(() => ({
  sec: currentSectionIdx,
  blocks: Array.from(document.querySelectorAll(".ls-section")).map((b) => b.dataset.sec),
  readCount: state.read.length,
  read0: state.read.includes(STUDY[0].id),
  read1: state.read.includes(STUDY[1].id),
  interstitial: !!document.querySelector(".section-done"),
  inlineComplete: document.querySelectorAll(".ls-complete").length,
  xp: state.xp,
  counter: document.getElementById("sec-counter")?.textContent,
}));
await page.screenshot({ path: `${outdir}/flow-final.png` });
console.log(JSON.stringify({ lastSnap: snap, res, errors: errors.slice(0, 6) }, null, 1));
await browser.close();
