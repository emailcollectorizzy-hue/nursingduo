// E2E: inline recall flow on Oral Antidiabetics — cloze renders, grading unlocks in place.
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

// open the Overview aspect of Oral Antidiabetics (the one the user found broken)
const setup = await page.evaluate(() => {
  const i = STUDY.findIndex((s) => /Oral Antidiabetics · Overview/i.test(s.title));
  state.read = STUDY.slice(0, i).map((x) => x.id);
  saveState();
  switchTab("study");
  goToSection(i);
  return {
    section: STUDY[i].title,
    recallHosts: document.querySelectorAll(".ls-recall").length,
    mounted: document.querySelectorAll(".rc-card").length,
    locked: document.querySelectorAll(".ls-chunk.ls-locked").length,
    promptText: (document.querySelector(".rc-prompt")?.textContent || "").slice(0, 80),
    promptEmpty: !((document.querySelector(".rc-prompt")?.textContent || "").trim()),
  };
});
console.log("setup:", JSON.stringify(setup, null, 1));

// scroll to the recall and shoot it
await page.evaluate(() => document.querySelector(".rc-card")?.scrollIntoView({ block: "center" }));
await page.waitForTimeout(600);
await page.screenshot({ path: `${outdir}/recall-inline.png` });

// reveal via space, grade first card "don't know" (m) to test requeue, rest with j
await page.keyboard.press(" ");
await page.waitForTimeout(400);
await page.screenshot({ path: `${outdir}/recall-revealed.png` });
const revealProbe = await page.evaluate(() => ({
  answerShown: !!document.querySelector(".rc-answer") && document.querySelector(".rc-answer").style.display !== "none",
  answerText: (document.querySelector(".rc-a-box")?.textContent || "").slice(0, 60),
  confBtns: document.querySelectorAll(".rc-card .conf-btn").length,
}));
await page.keyboard.press("m");
await page.waitForTimeout(600);
// grade through the rest with "knew it"
let guard = 0;
while (guard++ < 30) {
  const st = await page.evaluate(() => ({
    active: !!document.querySelector(".rc-card"),
    done: !!document.querySelector(".ls-recall-done"),
  }));
  if (!st.active || st.done) break;
  await page.keyboard.press(" ");
  await page.waitForTimeout(250);
  await page.keyboard.press("j");
  await page.waitForTimeout(450);
}
await page.waitForTimeout(800);
const after = await page.evaluate(() => {
  const s = STUDY[currentSectionIdx];
  return {
    recallDone: !!document.querySelector(".ls-recall-done"),
    locked: document.querySelectorAll(".ls-chunk.ls-locked").length,
    gateState: Object.keys(state.lessonGate).length,
    srsWrites: Object.keys(state.srs).filter((k) => k.startsWith("fc:")).length,
    nextMounted: document.querySelectorAll(".rc-card").length,
    scrollY: Math.round(window.scrollY),
  };
});
await page.screenshot({ path: `${outdir}/recall-passed.png` });
console.log(JSON.stringify({ revealProbe, after, errors: errors.slice(0, 6) }, null, 1));
await browser.close();
