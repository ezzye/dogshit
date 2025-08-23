import { test, expect } from '@playwright/test';

test('signed download links trigger downloads', async ({ page }) => {
  await page.route('**/summary/123', (route) =>
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        totals: { income: 100, expenses: 50, net: 50 },
        categories: [],
      }),
      headers: { 'content-type': 'application/json' },
    }),
  );
  await page.route('**/transactions/123', (route) =>
    route.fulfill({
      status: 200,
      body: JSON.stringify([]),
      headers: { 'content-type': 'application/json' },
    }),
  );
  await page.route('**/costs/123', (route) =>
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        tokens_in: 0,
        tokens_out: 0,
        total_tokens: 0,
        estimated_cost_gbp: 0,
      }),
      headers: { 'content-type': 'application/json' },
    }),
  );

  await page.route('**/report/123', (route) =>
    route.fulfill({
      status: 200,
      body: JSON.stringify({ url: '/download/123/report?sig=r123' }),
      headers: { 'content-type': 'application/json' },
    }),
  );
  await page.route('**/download/123/summary', (route) =>
    route.fulfill({
      status: 200,
      body: JSON.stringify({ url: '/download/123/summary?sig=s123' }),
      headers: { 'content-type': 'application/json' },
    }),
  );

  await page.route('**/download/123/report?sig=r123', (route) =>
    route.fulfill({
      status: 200,
      body: 'pdf',
      headers: {
        'content-type': 'application/pdf',
        'content-disposition': 'inline; filename="report.pdf"',
      },
    }),
  );
  await page.route('**/download/123/summary?sig=s123', (route) =>
    route.fulfill({
      status: 200,
      body: 'summary',
      headers: {
        'content-type': 'text/plain',
        'content-disposition': 'attachment; filename="summary.txt"',
      },
    }),
  );

  await page.goto('/results/123');

  await page.waitForResponse('**/download/123/report?sig=r123');
  const viewer = page.locator('iframe[title="Report"]');
  await expect(viewer).toHaveAttribute(
    'src',
    '/download/123/report?sig=r123',
  );

  const [summaryDownload] = await Promise.all([
    page.waitForEvent('download'),
    page.getByText('Download Summary').click(),
  ]);
  expect(summaryDownload.suggestedFilename()).toContain('summary');

  const [reportDownload] = await Promise.all([
    page.waitForEvent('download'),
    page.getByText('Download Report').click(),
  ]);
  expect(reportDownload.suggestedFilename()).toContain('report');
});

