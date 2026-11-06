// Run against a local MeCoBi server with the production frontend rebuilt:
// npx playwright test tests/error-rendering.spec.js --workers=1
// MECOBI_TEST_URL may override the default http://localhost:8000.
import { test, expect } from "@playwright/test";

const base = process.env.MECOBI_TEST_URL || "http://localhost:8000";
const payload = '<img src=x onerror="alert(123)">';
const csv = "Name,Metal,Charge,L1,L2,L3,L4\nDemo,Pt,2,N,N,[Cl-],[Cl-]";

async function openRow(page) {
  await page.goto(base);
  await page.locator("#csv").fill(csv);
  await page.getByRole("button", { name: "Parse", exact: true }).click();
  await page.getByRole("button", { name: "Assign", exact: true }).waitFor();
  await page.locator("#relax").uncheck();
}

test.beforeEach(async ({ page }) => {
  // Dismiss any unexpected alerts so failures do not leave the browser blocked.
  page.on("dialog", async (dialog) => {
    await dialog.dismiss();
    throw new Error(`Injected script executed: ${dialog.message()}`);
  });
});

test("real invalid notation is displayed literally", async ({ page }) => {
  await openRow(page);
  await page.getByRole("button", { name: /notation/ }).click();
  await page.locator(".notation-input").fill(payload);
  await page.getByRole("button", { name: "Build", exact: true }).click();
  await expect(page.locator(".pill-err")).toContainText(payload);
  await expect(page.locator('img[src="x"]')).toHaveCount(0);
});

for (const mode of ["assignment", "queue"]) {
  test(`${mode} submission errors are displayed literally`, async ({ page }) => {
    await openRow(page);
    await page.route(`**/api/${mode === "queue" ? "jobs" : "build"}`, route =>
      route.fulfill({ status: 422, json: { detail: payload } })
    );
    if (mode === "assignment") {
      await page.getByRole("button", { name: "Assign", exact: true }).click();
      await page.getByRole("button", { name: "Build this isomer", exact: true }).click();
    } else {
      await page.getByRole("button", { name: "Build all (queue job)", exact: true }).click();
    }
    await expect(page.locator(".pill-err").first()).toContainText(payload);
    await expect(page.locator('img[src="x"]')).toHaveCount(0);
  });
}

for (const status of ["failed", "missing", "done"]) {
  test(`queued ${status} status preserves text and formatting`, async ({ page }) => {
    await openRow(page);
    let finish = false;
    await page.route("**/api/jobs", route =>
      route.fulfill({ status: 202, json: { job_id: "abcdef", estimate_s: 30 } })
    );
    await page.route("**/api/jobs/abcdef", route => {
      const terminal = status === "missing" ? { detail: payload } : {
        status, results: [], error: payload,
        complex_errors: [{ complex: `Name ${payload}`, error: `Error ${payload}` }],
      };
      return route.fulfill({ json: finish ? terminal : {
        status: "running", progress: 0.25, stage: payload, results: [],
      } });
    });
    await page.getByRole("button", { name: "Build all (queue job)", exact: true }).click();
    await expect(page.getByTitle("25%", { exact: true })).toBeVisible();
    await expect(page.locator(".mono").filter({ hasText: payload })).toBeVisible();
    await expect(page.locator('img[src="x"]')).toHaveCount(0);
    finish = true;
    if (status === "done") {
      await expect(page.locator(".pill-err")).toContainText("1 complex(es) failed");
      await expect(page.locator("li").filter({ hasText: payload })).toContainText(`Name ${payload}: Error ${payload}`);
    } else {
      await expect(page.locator(".pill-err")).toContainText(payload);
    }
    await expect(page.locator('img[src="x"]')).toHaveCount(0);
    await page.getByRole("button", { name: "Dismiss", exact: true }).click();
    await expect(page.getByRole("button", { name: "Dismiss", exact: true })).toHaveCount(0);
    expect(new URL(page.url()).hash).toBe("");
  });
}
