// Screenshot helper: node shot.mjs <file.html> <outdir> [tab] [theme] [width] [height]
import { chromium } from "playwright";
import { pathToFileURL } from "url";

const [file, outdir, tab = "home", theme = "dark", w = "1024", h = "768"] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: +w, height: +h } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
await page.goto(pathToFileURL(file).href);
// dismiss first-run tour by marking it seen, then reload
await page.evaluate(() => {
  try {
    const k = Object.keys(localStorage).find((x) => x.startsWith("quizpage:"));
    const s = k ? JSON.parse(localStorage.getItem(k) || "{}") : {};
    s.tourSeen = true; s.tourDone = true; s.seenTour = true;
    if (k) localStorage.setItem(k, JSON.stringify(s));
  } catch (e) {}
});
await page.reload();
await page.waitForTimeout(600);
await page.evaluate(() => {
  document.querySelectorAll(".tour-overlay, .qp-modal, .qp-modal-scrim, [class*='tour']").forEach((n) => {
    if (n.closest("button")) return;
    if (/tour|modal/i.test(n.className)) n.remove();
  });
});
await page.evaluate((t) => {
  try { state.dark = t === "dark"; state.darkSet = true; applyTheme(); } catch (e) {}
}, theme);
if (tab !== "home") {
  await page.evaluate((t) => { try { switchTab(t); } catch (e) {} }, tab);
  await page.waitForTimeout(600);
}
await page.screenshot({ path: `${outdir}/${tab}-${theme}-${w}.png`, fullPage: false });
console.log(JSON.stringify({ shot: `${tab}-${theme}-${w}.png`, errors: errors.slice(0, 5) }));
await browser.close();
