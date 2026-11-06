// Browser stress test of the MeCoBi React GUI via Playwright: fills the CSV,
// parses, builds a few rows, exercises the donor panel / 3D assign scene / queued
// "Build all", toggles theme, and reports console + page errors and screenshots.
//
// Usage (server must be running; needs `npm i playwright` + a Chromium):
//   MECOBI_URL=http://127.0.0.1:8000 STRESS_CSV=tests/fixtures/test_compounds.csv \
//   SHOTS_DIR=./shots node scripts/stress_ui.mjs
import { chromium } from "playwright";
import { readFileSync } from "fs";

const BASE = process.env.MECOBI_URL || "http://127.0.0.1:8000";
const SHOTS = process.env.SHOTS_DIR || ".";
const CSV = readFileSync(process.env.STRESS_CSV, "utf8");

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });

const consoleErrors = [], pageErrors = [];
page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
page.on("pageerror", (e) => pageErrors.push(String(e)));

const log = (...a) => console.log(...a);
let step = 0;
const shot = async (name) => { await page.screenshot({ path: `${SHOTS}/${String(++step).padStart(2,"0")}-${name}.png`, fullPage: true }); };

try {
  await page.goto(BASE, { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForSelector("#csv", { timeout: 15000 });
  log("TITLE:", await page.title(), "| header:", (await page.locator("header").first().innerText()).replace(/\n+/g," ").slice(0,80));

  // Inject the big stress CSV into the textarea and parse.
  await page.locator("#csv").fill(CSV);
  const t0 = Date.now();
  await page.getByRole("button", { name: "Parse" }).click();
  await page.waitForSelector("table tbody tr", { timeout: 90000 });
  log(`PARSE took ${((Date.now()-t0)/1000).toFixed(1)}s`);

  // Row / control census.
  const dataRows = await page.locator("table tbody tr").count();
  log("TABLE rows (incl. donor sub-rows):", dataRows);
  log("Geometry selects:", await page.locator("table select").count());
  log("Warning/unsupported chips:", await page.locator("table .chip.warn, table .badge-unsupported, table .unsupported").count());
  // Count rows that mention an error/unsupported state (text scan).
  const bodyText = await page.locator("table tbody").innerText();
  const unsupportedHits = (bodyText.match(/could not parse|unsupported|no supported/gi) || []).length;
  log("Rows showing parse errors (text scan):", unsupportedHits);
  await shot("parsed-batch");

  // Turn off relax so builds are fast (assembly only).
  const relax = page.locator("#relax");
  if (await relax.count()) { if (await relax.isChecked()) await relax.uncheck(); }

  // Build the first few buildable complexes via per-row Build.
  const buildButtons = page.getByRole("button", { name: "Build", exact: true });
  const nBuild = Math.min(4, await buildButtons.count());
  log(`Building first ${nBuild} rows (relax off)...`);
  for (let i = 0; i < nBuild; i++) {
    await buildButtons.nth(i).click();
    await page.waitForTimeout(200);
  }
  await page.waitForSelector(".result-item", { timeout: 120000 });
  await page.waitForFunction((n) => document.querySelectorAll(".result-item").length >= n, nBuild, { timeout: 120000 }).catch(()=>{});
  log("RESULT items after per-row builds:", await page.locator(".result-item").count());
  await page.waitForTimeout(2500); // let 3Dmol viewers render
  await shot("built-rows");

  // Donor-correction panel on a metallocene row (Ferrocene) — untick "donors ok?".
  try {
    const cbs = page.locator('table tbody tr input[type="checkbox"]');
    await cbs.nth(1).uncheck();
    await page.waitForSelector(".donor-panel svg", { timeout: 20000 });
    log("Donor panel SVGs:", await page.locator(".donor-panel svg").count());
    await shot("donor-panel");
    await cbs.nth(1).check();
  } catch (e) { log("DONOR PANEL step:", String(e).slice(0,120)); }

  // 3D isomer Assign scene on an octahedral row.
  try {
    const assign = page.getByRole("button", { name: "Assign" });
    log("Assign buttons present:", await assign.count());
    // find an enabled one (metallocenes are greyed out)
    let opened = false;
    for (let i = 0; i < await assign.count(); i++) {
      if (await assign.nth(i).isEnabled()) { await assign.nth(i).click(); opened = true; break; }
    }
    if (opened) {
      await page.waitForSelector(".scene-panel .scene-wrap canvas", { timeout: 20000 });
      await page.waitForTimeout(1000);
      log("Scene site labels:", await page.locator(".scene-panel .vertex-label.clickable").count(),
          "| palette chips:", await page.locator(".scene-panel .palette-chip").count());
      await shot("assign-scene");
    } else log("No enabled Assign button found");
  } catch (e) { log("ASSIGN step:", String(e).slice(0,120)); }

  // "Build all (queue job)" over the whole batch — exercises the async job path.
  try {
    const buildAll = page.getByRole("button", { name: /Build all/i });
    if (await buildAll.count()) {
      await buildAll.first().click();
      // poll for job progress / completion up to 90s
      const done = await page.waitForFunction(() => {
        const t = document.body.innerText;
        return /done|complete|finished|\/\s*\d+\s+built/i.test(t) || document.querySelectorAll(".result-item").length > 5;
      }, null, { timeout: 90000 }).then(()=>true).catch(()=>false);
      log("Build-all job reached completion signal:", done);
      await shot("build-all-job");
    } else log("No 'Build all' button");
  } catch (e) { log("BUILD-ALL step:", String(e).slice(0,120)); }

  // Dark theme.
  try {
    await page.getByRole("button", { name: /Dark|Light/ }).first().click();
    await page.waitForTimeout(400);
    await shot("dark");
  } catch (e) { log("THEME step:", String(e).slice(0,80)); }

} catch (e) {
  log("SCRIPT ERROR:", String(e));
  await shot("error-state");
} finally {
  log("CONSOLE ERRORS:", consoleErrors.length, JSON.stringify(consoleErrors.slice(0, 10)));
  log("PAGE ERRORS:", pageErrors.length, JSON.stringify(pageErrors.slice(0, 10)));
  await browser.close();
}
