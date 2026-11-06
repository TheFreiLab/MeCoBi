import { test, expect } from '@playwright/test';
const base = process.env.MECOBI_TEST_URL || 'http://localhost:8000';

test('public busy notice shows limits and long running warning', async ({ page }) => {
  await page.route('**/api/workload', route => route.fulfill({ json: {
    busy: true, queued_jobs: 2, running_jobs: 1, pending_complexes: 900,
    estimated_wait_s: 1200, longest_running_s: 700, long_job_seconds: 600,
    max_complexes_per_job: 1000, max_pending_complexes: 1000,
  }}));
  await page.goto(base);
  await expect(page.getByText('A long job is running.', { exact: true })).toBeVisible();
  await expect(page.getByText(/1,000 complexes per job/)).toBeVisible();
  await expect(page.getByRole('status')).toContainText('about 20 minute(s)');
});

test('private long job link restores status without reparsing input', async ({ page }) => {
  await page.route('**/api/jobs/abcdef0123456789', route => route.fulfill({ json: {
    job_id: 'abcdef0123456789', status: 'running', estimate_s: 1200,
    progress: 0.25, results: [], stage: 'building',
  }}));
  await page.goto(base + '/#job=abcdef0123456789');
  await expect(page.getByText(/This is a long job/)).toBeVisible();
  await expect(page.getByRole('link', { name: 'Keep this private job link' })).toHaveAttribute('href', '#job=abcdef0123456789');
});

test('interrupted job link retains completed structure downloads', async ({ page }) => {
  await page.route('**/api/jobs/abcdef', route => route.fulfill({ json: {
    job_id: 'abcdef', status: 'failed', error: 'Interrupted by server shutdown.',
    results: [{ name: 'completed.xyz', token: 'abcdef/completed.xyz', total_charge: 0,
                uhf: 0, warnings: [], formats: ['xyz'] }],
  }}));
  await page.route('**/api/file/abcdef/completed.xyz', route => route.fulfill({
    contentType: 'text/plain', body: '1\ncompleted\nH 0 0 0\n',
  }));
  await page.goto(base + '/#job=abcdef');
  await expect(page.getByText('Job failed: Interrupted by server shutdown.')).toBeVisible();
  await expect(page.getByTitle('completed.xyz', { exact: true })).toBeVisible();
  await expect(page.locator('a[href="/api/file/abcdef/completed.xyz"]')).toBeVisible();
});
