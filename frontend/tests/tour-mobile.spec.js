import { test, expect, devices } from '@playwright/test';
const base = process.env.MECOBI_TEST_URL || 'http://localhost:8000';

// The guided tour on a phone: the table scrolls sideways under a sticky Build column and
// the donor panel / 3D editor are taller than the screen. Each step must leave the control
// it asks for visible and tappable, not hidden under the sticky column or the tour card.
// Needs a live backend (Parse). Run on WebKit to match iPhone Safari:
//   MECOBI_TEST_URL=http://localhost:5173 npx playwright test tests/tour-mobile.spec.js --browser=webkit
const { defaultBrowserType, ...iphone } = devices['iPhone 13'];
test.use(iphone);
test.setTimeout(240_000);

// True when the element's centre is on screen and is what a tap there would hit.
const tappable = (loc) => loc.evaluate((el) => {
  const b = el.getBoundingClientRect();
  const x = b.left + b.width / 2, y = b.top + b.height / 2;
  if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) return `off-screen at ${x},${y}`;
  const hit = document.elementFromPoint(x, y);
  return hit && (hit === el || el.contains(hit)) ? true : `covered by ${hit?.className || hit?.tagName}`;
});
const title = (page) => page.locator('.tour-title');
const settle = (page) => page.waitForTimeout(1200); // smooth scroll + ring transition

test('tour keeps each interactive control tappable on an iPhone', async ({ page }) => {
  await page.goto(base);
  await page.getByRole('button', { name: /^Tour$/ }).first().tap();
  const next = page.locator('.tour-tooltip button.primary');
  while (!/Parse/.test(await title(page).textContent())) await next.tap();
  await page.getByRole('button', { name: 'Parse', exact: true }).tap();
  await expect(title(page)).toHaveText(/Review the table/, { timeout: 180_000 });
  await next.tap();

  // Donors checkbox: was scrolled to sit under the sticky Build column.
  await expect(title(page)).toHaveText(/Donor atoms/);
  await settle(page);
  const donors = page.locator('[data-tour="ferroquine-donors"]');
  await expect.poll(() => tappable(donors), { timeout: 10_000 }).toBe(true);
  await donors.tap();

  // Donor panel: the ring was drawn around the 1000 px-wide cell, and ✓ was off-screen.
  await expect(title(page)).toHaveText(/Cp rings/);
  await settle(page);
  const ring = await page.locator('.tour-highlight').boundingBox();
  expect(ring.x).toBeGreaterThanOrEqual(-10);
  expect(ring.x + ring.width).toBeLessThanOrEqual(iphone.viewport.width + 10);
  const save = page.locator('[data-tour="donor-panel"] button[aria-label="Save selection"]');
  await expect.poll(() => tappable(save), { timeout: 10_000 }).toBe(true);
  await save.tap();

  await expect(title(page)).toHaveText(/Relaxation/);
  await next.tap();
  await page.locator('[data-tour="assign-btn"]').tap();
  await expect(title(page)).toHaveText(/clean slate/);
  await settle(page);
  await page.locator('[data-tour="assign-disconnect"]').tap();

  // 3D editor: the card covered the lower sites.
  await expect(title(page)).toHaveText(/Place the ligands/);
  await settle(page);
  for (const sid of [0, 1, 2, 3]) {
    const site = page.locator(`.vertex-label[data-sid="${sid}"]`);
    await expect.poll(() => tappable(site), { timeout: 10_000, message: `site ${sid}` }).toBe(true);
    await site.tap();
    await page.waitForTimeout(300);
  }

  await expect(title(page)).toHaveText(/Save this isomer/);
  await settle(page);
  await expect.poll(() => tappable(page.locator('[data-tour="assign-build"]')), { timeout: 10_000 }).toBe(true);
});
