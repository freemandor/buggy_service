import { test, expect } from '@playwright/test';

test('driver route stays consistent while polling', async ({ page }) => {
  await page.goto('/login');

  await page.getByLabel('Username').fill('driver1');
  await page.getByLabel('Password').fill('driver1');
  await page.getByRole('button', { name: 'Login' }).click();

  await page.waitForURL('**/driver');
  await expect(page.getByRole('heading', { name: 'My route' })).toBeVisible();

  const firstCard = page.locator('.stop-card').first();
  await expect(firstCard).toBeVisible();

  const startButton = firstCard.getByRole('button', { name: 'Start' });
  await startButton.click();

  const statusPill = firstCard.locator('.pill--status');
  const completeButton = firstCard.getByRole('button', { name: 'Complete' });

  await expect(statusPill).toHaveText('ON_ROUTE', { timeout: 5000 });
  await expect(completeButton).toBeVisible({ timeout: 5000 });

  // Let the polling interval run a couple of times; state should remain stable.
  await page.waitForTimeout(4000);
  await expect(statusPill).toHaveText('ON_ROUTE');
  await expect(completeButton).toBeVisible();
});
