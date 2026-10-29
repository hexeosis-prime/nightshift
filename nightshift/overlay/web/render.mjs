// node render.mjs <data.json> <outdir> [from] [to]  ->  transparent PNG frames f00000.png ...
// Chromium: the one Playwright installed (npx playwright install chromium), or NIGHTSHIFT_CHROME=<path to chrome>.
import { chromium } from "playwright-core";
import { readFileSync, mkdirSync, writeFileSync, existsSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const [dataPath, outDir, from = "0", to] = process.argv.slice(2);
if (!dataPath || !outDir) { console.error("usage: node render.mjs data.json outdir [from] [to]"); process.exit(2); }
const data = JSON.parse(readFileSync(dataPath, "utf8"));
mkdirSync(outDir, { recursive: true });
const opts = { args: ["--allow-file-access-from-files"] };
if (process.env.NIGHTSHIFT_CHROME && existsSync(process.env.NIGHTSHIFT_CHROME)) opts.executablePath = process.env.NIGHTSHIFT_CHROME;
function candidates() {      // any Chromium a Playwright install left behind, then system browsers
  const out = [];
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH, "/opt/pw-browsers", resolve(homedir(), ".cache/ms-playwright"),
                 resolve(homedir(), "Library/Caches/ms-playwright"), process.env.LOCALAPPDATA && resolve(process.env.LOCALAPPDATA, "ms-playwright")].filter(Boolean);
  for (const r of roots) {
    if (!existsSync(r)) continue;
    for (const d of readdirSync(r).filter(d => d.startsWith("chromium")).sort().reverse())
      for (const exe of ["chrome-linux/chrome", "chrome-linux64/chrome", "chrome-win/chrome.exe", "chrome-win64/chrome.exe",
                         "chrome-mac/Chromium.app/Contents/MacOS/Chromium", "chrome-headless-shell-linux64/chrome-headless-shell"])
        out.push(resolve(r, d, exe));
  }
  return out.concat(["/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
                     "C:/Program Files/Google/Chrome/Application/chrome.exe", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]);
}
let browser;
try { browser = await chromium.launch(opts); }
catch (e) {
  const exe = candidates().find(existsSync);
  if (!exe) throw e;
  browser = await chromium.launch({ ...opts, executablePath: exe });
}
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.on("pageerror", e => console.error("page error:", e.message));
await page.goto(pathToFileURL(resolve(here, "overlay.html")).href);
const fontsOk = await page.evaluate(d => window.init(d), data);
if (!fontsOk) console.error("warning: fonts not loaded (run npm install in nightshift/overlay/web)");
const end = to ? +to : data.frames;
const t0 = Date.now();
for (let f = +from; f < end; f++) {
  const url = await page.evaluate(f => window.renderAt(f), f);
  writeFileSync(`${outDir}/f${String(f).padStart(5, "0")}.png`, Buffer.from(url.slice(url.indexOf(",") + 1), "base64"));
}
console.log(`rendered ${end - +from} frames in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
await browser.close();
