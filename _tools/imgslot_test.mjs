// Verify the Find & Paste image-slot widget: placeholder → widget → search URL → paste → persist.
import { chromium } from "playwright";
import { pathToFileURL } from "url";

const [file] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1024, height: 800 } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto(pathToFileURL(file).href);
await page.evaluate(() => { localStorage.clear(); localStorage.setItem("quizpage:tour-done", "1"); });
await page.reload();
await page.waitForTimeout(500);

const r = await page.evaluate(() => {
  // build a synthetic study block with a placeholder <p>, hydrate it
  const host = document.createElement("div");
  host.innerHTML = '<p><strong>📷 Find &amp; paste — [Pathology]:</strong> cross-section of an inflamed bronchus in asthma showing mucus and bronchoconstriction</p>';
  document.body.appendChild(host);
  hydrateImageSlots(host, "Asthma · Context & Patho");
  const slot = host.querySelector(".img-slot");
  const out = { hydrated: !!slot, empty: !!slot.querySelector(".img-slot-empty") };
  out.desc = slot.querySelector(".img-slot-desc")?.textContent.slice(0, 50);
  out.cat = slot.querySelector(".eyebrow")?.textContent;
  // search url
  const link = slot.querySelector(".img-slot-link");
  let opened = null;
  window.open = (u) => { opened = u; };
  link.click();
  out.searchUrl = opened;
  // simulate storing an image via PI.set, re-render, expect <img>
  const key = slot.dataset.imgkey;
  PI.set(key, "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==");
  renderImageSlot(slot);
  out.nowFilled = !!slot.querySelector("figure img");
  out.imgSrcOk = (slot.querySelector("figure img")?.src || "").startsWith("data:image");
  // persisted in dedicated localStorage key (NOT in synced state)
  const lsKey = Object.keys(localStorage).find((k) => k.startsWith("quizpage:img:"));
  out.persistedKey = lsKey;
  out.persisted = !!(lsKey && JSON.parse(localStorage.getItem(lsKey))[key]);
  out.inState = JSON.stringify(state).includes("data:image"); // should be FALSE (not bloating synced state)
  // remove
  slot.querySelector(".img-slot-remove").click();
  out.afterRemoveEmpty = !!slot.querySelector(".img-slot-empty");
  host.remove();
  return out;
});
console.log(JSON.stringify(r, null, 1));
console.log("errors:", JSON.stringify(errors.slice(0, 5)));
await browser.close();
