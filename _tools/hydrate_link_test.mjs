import { chromium } from "playwright";
import { pathToFileURL } from "url";
const [file] = process.argv.slice(2);
const b = await chromium.launch();
const p = await b.newPage();
const errs = [];
p.on("pageerror", (e) => errs.push(String(e)));
await p.goto(pathToFileURL(file).href);
await p.evaluate(() => { localStorage.clear(); localStorage.setItem("quizpage:tour-done", "1"); });
await p.reload();
await p.waitForTimeout(400);
const r = await p.evaluate(() => {
  const h = document.createElement("div");
  // placeholder + the Obsidian search link joined in one paragraph (the _imglinks.py case)
  h.innerHTML = '<p><strong>\u{1F4F7} Find &amp; paste — [Pathology]:</strong> inflamed bronchus in asthma showing mucus plugging '
    + '<a href="https://www.google.com/search?udm=2&q=inflamed+bronchus">\u{1F50D} Search images</a></p>';
  document.body.appendChild(h);
  hydrateImageSlots(h, "Asthma");
  const slot = h.querySelector(".img-slot");
  const desc = slot.querySelector(".img-slot-desc").textContent;
  const link = slot.querySelector(".img-slot-link");
  let opened = null; window.open = (u) => { opened = u; };
  link.click();
  const out = { desc, descClean: desc.indexOf("Search") < 0 && desc.indexOf("\u{1F50D}") < 0,
                searchUrl: opened, strayGoogleLink: !!h.querySelector("a[href*=google]") };
  h.remove();
  return out;
});
console.log(JSON.stringify(r, null, 1));
console.log("errors:", JSON.stringify(errs.slice(0, 3)));
await b.close();
