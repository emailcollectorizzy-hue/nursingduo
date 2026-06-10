import { chromium } from "playwright";
import { pathToFileURL } from "url";
const [file, out, theme = "light"] = process.argv.slice(2);
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1024, height: 950 } });
await p.goto(pathToFileURL(file).href);
await p.evaluate(() => { localStorage.clear(); localStorage.setItem("quizpage:tour-done", "1"); });
await p.reload();
await p.waitForTimeout(700);
await p.evaluate((t) => { state.dark = t === "dark"; state.darkSet = true; applyTheme(); }, theme);
// open the Biguanides/Metformin section (has an OpenStax figure)
await p.evaluate(() => {
  const i = STUDY.findIndex((s) => /<img/i.test(s.html));
  state.read = STUDY.slice(0, i).map((x) => x.id); saveState();
  switchTab("study"); goToSection(i);
});
await p.waitForTimeout(500);
await p.evaluate(() => { const im = document.querySelector(".lesson-card img"); if (im) im.scrollIntoView({ block: "center" }); });
// wait for the image to actually load
await p.waitForFunction(() => { const im = document.querySelector(".lesson-card img"); return im && im.complete && im.naturalWidth > 0; }, { timeout: 15000 }).catch(() => {});
await p.waitForTimeout(500);
const info = await p.evaluate(() => {
  const im = document.querySelector(".lesson-card p:has(> img:only-child) > img");
  if (!im) return { noImg: true };
  const par = im.closest("p"); const cs = getComputedStyle(par);
  return { natW: im.naturalWidth, renderW: Math.round(im.getBoundingClientRect().width), parentBg: cs.backgroundColor, parentBorder: cs.borderTopWidth, parentPad: cs.padding };
});
await p.screenshot({ path: out });
console.log(JSON.stringify(info));
await b.close();
