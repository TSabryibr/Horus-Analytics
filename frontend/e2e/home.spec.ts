import { test, expect } from '@playwright/test';
import { primeHorusBoot, waitForShellReady } from './helpers';

test.beforeEach(async ({ page }) => {
    await primeHorusBoot(page);
});

test('has title', async ({ page }) => {
    await page.goto('/');

    // Expect a title "to contain" a substring.
    await expect(page).toHaveTitle(/Horus Analytics/);
});

test('dashboard loads', async ({ page }) => {
    await page.goto('/');
    await waitForShellReady(page);

    // Check for the flagship Home center of gravity.
    await expect(page.getByRole('main').getByText(/Surveillance Active|Intervention Required|Conviction Leading|Quiet Vigil/i)).toBeVisible();
    await expect(page.getByRole('main').getByText(/Daily Signal Desk/i)).toBeVisible();
    await expect(page.getByRole('main').getByText(/Performance Analytics/i)).toBeVisible();

    // Check the redesigned command ribbon chrome is visible.
    await expect(page.getByLabel('Intelligence navigation group')).toBeVisible();
    await expect(page.getByTestId('command-ribbon-grid').locator('a[href="/telegram"]').first()).toBeVisible();
});
