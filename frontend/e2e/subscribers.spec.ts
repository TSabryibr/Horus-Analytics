import { test, expect } from '@playwright/test';

import { primeHorusBoot, waitForShellReady } from './helpers';

const API_BASE = 'http://127.0.0.1:8100';

test.describe('Subscribers commercial workflow', () => {
  test.beforeEach(async ({ page }) => {
    await primeHorusBoot(page);
  });

  test('creates a managed subscriber, links a portfolio, previews advisory, and opens delivery ledger', async ({ page, request }) => {
    test.setTimeout(180000);

    const stamp = Date.now();
    const subscriberName = `E2E Managed ${stamp}`;
    const portfolioName = `E2E Portfolio ${stamp}`;

    await expect
      .poll(async () => {
        const response = await request.get(`${API_BASE}/api/v1/health`, { timeout: 5000 }).catch(() => null);
        return response?.status() ?? 0;
      }, { timeout: 60000, message: 'backend health should be ready before subscriber setup' })
      .toBe(200);

    const portfolioResponse = await request.post(`${API_BASE}/api/v1/portfolios`, {
      data: { name: portfolioName, auto_manage: false },
      timeout: 30000,
    });
    expect(portfolioResponse.ok()).toBeTruthy();
    const portfolio = await portfolioResponse.json();
    expect(portfolio.id).toBeTruthy();

    await page.goto('/subscribers', { waitUntil: 'domcontentloaded', timeout: 90000 });
    await waitForShellReady(page);

    await expect(page.getByRole('heading', { name: 'Subscribers' })).toBeVisible();
    await page.getByRole('button', { name: /Add Subscriber/i }).click();
    await page.getByLabel(/Subscriber Name/i).fill(subscriberName);
    await page.getByLabel(/Subscription Tier/i).selectOption('MANAGED_ADVISORY');
    await page.getByLabel(/Subscriber Private Chat ID/i).fill('-100999001');
    await page.getByLabel(/Paid Until/i).fill('2027-12-31');
    await page.getByLabel(/Linked Portfolio/i).selectOption(String(portfolio.id));
    await page.getByRole('button', { name: /Save Subscriber/i }).click();

    const subscriberRow = page
      .locator('article')
      .filter({ hasText: subscriberName })
      .filter({ hasText: /Last delivery/i })
      .first();
    await expect(subscriberRow).toBeVisible({ timeout: 45000 });
    await expect(subscriberRow.getByText('Type 3 Managed Advisory')).toBeVisible();
    await expect(subscriberRow.getByText(portfolioName)).toBeVisible();
    await expect(subscriberRow.getByText(/Last delivery: None/i)).toBeVisible();

    await subscriberRow.getByRole('button', { name: new RegExp(`Generate ${subscriberName} advisory`, 'i') }).click();
    await expect(page.getByRole('heading', { name: 'Advisory Preview' })).toBeVisible();
    await expect(page.getByText(subscriberName).last()).toBeVisible({ timeout: 45000 });
    await expect(page.getByText(/action item\(s\)/i)).toBeVisible();
    await expect(page.getByText(/Advisory only/i)).toBeVisible();

    await subscriberRow.getByRole('button', { name: new RegExp(`Inspect ${subscriberName} deliveries`, 'i') }).click();
    await expect(page.getByRole('heading', { name: 'Delivery Ledger' })).toBeVisible();
    await expect(page.getByText('No delivery attempts recorded for this subscriber.')).toBeVisible({ timeout: 45000 });
  });
});
