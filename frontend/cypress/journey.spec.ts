import { test, expect } from '@playwright/test';

// Three-click journey: upload -> progress -> results

test('user can upload file and reach results', async ({ page }) => {
  await page.route('/rules', route => route.fulfill({ json: ['rule one'] }));
  await page.goto('/');

  await page.route('/upload', route => route.fulfill({ json: { job_id: '123' } }));
  await page.route('/status/123', route => route.fulfill({ json: { status: 'completed' } }));
  await page.route('/download/123/summary', route => route.fulfill({ body: 'summary' }));
  await page.route('/download/123/details', route => route.fulfill({ body: 'details' }));

  const filePath = 'index.html';
  await page.setInputFiles('input[type="file"]', filePath);
  await page.getByRole('button', { name: /upload/i }).click();

  await page.waitForURL('**/progress/123');
  await expect(page.getByRole('status')).toBeVisible();

  await page.waitForURL('**/results/123');
  await expect(page.getByRole('link', { name: /summary/i })).toBeVisible();
  await expect(page.getByRole('link', { name: /details/i })).toBeVisible();
});
