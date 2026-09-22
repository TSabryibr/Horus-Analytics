import { test, expect } from '@playwright/test';

import { primeHorusBoot, waitForShellReady } from './helpers';

test.beforeEach(async ({ page }) => {
    await primeHorusBoot(page);
});

test('settings exposes execution gate and strategy jump controls', async ({ page }) => {
    await page.goto('/settings', { waitUntil: 'domcontentloaded', timeout: 90000 });
    await waitForShellReady(page);

    const main = page.getByRole('main').first();
    await expect(page.getByRole('heading', { name: /Settings Command Deck/i }).first()).toBeVisible({ timeout: 45000 });
    const executionStrip = page.getByLabel('Execution command strip');
    await expect(executionStrip.getByRole('heading', { name: 'Execution Gate' })).toBeVisible();
    await expect(main.getByRole('link', { name: /Jump to Strategy & Risk/i })).toBeVisible();
    await expect(executionStrip.getByText(/AUTO_ENTRY|MANUAL_ARM|AUTO_OFF/)).toBeVisible();
});
