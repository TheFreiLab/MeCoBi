// Run against a local MeCoBi server with the production frontend rebuilt:
// npx playwright test tests/csv-upload.spec.js --workers=1
// MECOBI_TEST_URL may override the default http://localhost:8000.
import { test, expect } from "@playwright/test";

const base = process.env.MECOBI_TEST_URL || "http://localhost:8000";
const csv = "Name,Metal,Charge,L1,L2,L3,L4\nDemo,Pt,2,N,N,[Cl-],[Cl-]";

async function upload(page, file) {
  await page.goto(base);
  await page.locator('input[type="file"]').setInputFiles(file);
}

test("a real .csv is loaded into the paste box and parsed", async ({ page }) => {
  await upload(page, { name: "ok.csv", mimeType: "text/csv", buffer: Buffer.from(csv) });
  await expect(page.locator("#csv")).toHaveValue(csv);
  // The first parse on a fresh server loads the pydentate models; allow for that.
  await expect(page.getByRole("button", { name: /^Isomer editor/ })).toBeVisible({ timeout: 60_000 });
});

test("a .csv reported as Excel (Windows) is accepted", async ({ page }) => {
  await upload(page, {
    name: "excel.csv", mimeType: "application/vnd.ms-excel", buffer: Buffer.from(csv),
  });
  await expect(page.locator("#csv")).toHaveValue(csv);
});

const rejected = [
  ["wrong extension", { name: "ligands.txt", mimeType: "text/plain", buffer: Buffer.from(csv) },
    "Please upload a .csv file."],
  ["non-text type", { name: "ligands.csv", mimeType: "image/png", buffer: Buffer.from(csv) },
    "doesn't look like a CSV"],
  ["over the size cap", { name: "big.csv", mimeType: "text/csv", buffer: Buffer.alloc(4_000_001, "a") },
    "File too large"],
  ["binary renamed to .csv", {
    name: "evil.csv", mimeType: "text/csv", buffer: Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x00, 0xff]),
  }, "isn't plain text"],
];

for (const [label, file, message] of rejected) {
  test(`upload rejects ${label} without touching the paste box`, async ({ page }) => {
    await upload(page, file);
    await expect(page.locator(".pill-err")).toContainText(message);
    await expect(page.locator("#csv")).toHaveValue("");
  });
}
