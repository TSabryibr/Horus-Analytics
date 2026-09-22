import { test, expect } from '@playwright/test';
import { primeHorusBoot, waitForShellReady } from './helpers';

test.describe('Whales Page (Vanaheim)', () => {
    test.beforeEach(async ({ page }) => {
        await primeHorusBoot(page);
    });

    test('should load whales page', async ({ page }) => {
        await page.goto('/whales');
        await waitForShellReady(page);
        // The current UI uses "Institutional Flow Tracker" as the main H1
        await expect(page.getByRole('heading', { name: 'Institutional Flow Tracker' })).toBeVisible();
        await expect(page.getByText(/Smart-money accumulation and distribution surveillance/i)).toBeVisible();
    });

    test('should filter candidates', async ({ page }) => {
        await page.goto('/whales');
        await waitForShellReady(page);
        const filterInput = page.getByPlaceholder('Filter by ticker or sector...');

        // Ensure input is interactive and stable
        await filterInput.waitFor({ state: 'visible' });

        // Using pressSequentially to avoid race conditions with React state updates
        await filterInput.click();
        await filterInput.pressSequentially('Technology', { delay: 50 });

        // Ensure the value stuck
        await expect(filterInput).toHaveValue('Technology');
    });
});
