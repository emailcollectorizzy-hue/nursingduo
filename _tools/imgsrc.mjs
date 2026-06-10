import { chromium } from "playwright";
import { pathToFileURL } from "url";
const [file] = process.argv.slice(2);
const b = await chromium.launch();
const p = await b.newPage();
await p.goto(pathToFileURL(file).href);
const srcs = await p.evaluate(() => {
  const out = [];
  for (const s of STUDY) {
    const m = s.html.match(/<img[^>]*src="([^"]*)"/i);
    if (m) { out.push(m[1].slice(0, 100)); if (out.length >= 6) break; }
  }
  return { count: STUDY.filter((s) => /<img/i.test(s.html)).length, samples: out };
});
console.log(JSON.stringify(srcs, null, 1));
await b.close();
