import { test, expect } from '@playwright/test';

test('submitting rule feedback posts to /feedback', async ({ page }) => {
  await page.route('**/rules', (route) => {
    if (route.request().resourceType() === 'document') {
      return route.continue();
    }
    return route.fulfill({
      status: 200,
      body: JSON.stringify([
        {
          id: 1,
          label: 'Food',
          pattern: 'Tesco',
          match_type: 'contains',
          field: 'description',
          priority: 1,
          confidence: 1,
          version: 1,
          provenance: 'test',
          updated_at: 'now',
        },
      ]),
      headers: { 'content-type': 'application/json' },
    });
  });

  await page.route('**/feedback', (route) =>
    route.fulfill({ status: 200 }),
  );

  const feedbackRequest = page.waitForRequest('**/feedback');

  await page.goto('/rules');
  await page.getByLabel('Suggestion').fill('Groceries');
  await page.getByRole('button', { name: 'Suggest correction' }).click();

  const request = await feedbackRequest;
  expect(request.method()).toBe('POST');
  expect(request.postDataJSON()).toEqual({
    rule_id: 1,
    suggestion: 'Groceries',
  });
});
