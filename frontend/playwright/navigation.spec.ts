import { test, expect } from '@playwright/test';

test('home navigation to upload and rules', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Upload' }).first().click();
  await expect(page).toHaveURL(/\/upload$/);
  await page.goBack();
  await page.getByRole('link', { name: 'Rules' }).first().click();
  await expect(page).toHaveURL(/\/rules$/);
});
