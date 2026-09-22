import { test, expect } from '@playwright/test';
import { collectFatalConsoleErrors, primeHorusBoot, waitForShellReady } from './helpers';

test.describe('Horus Analytics E2E Tab Crawl', () => {
    test.beforeEach(async ({ page }) => {
        await primeHorusBoot(page);
    });

    const routes = [
        { label: 'Terminal Dashboard', href: '/' },
        { label: 'Release Rail', href: '/telegram' },
        { label: 'Market Scanner', href: '/scanner' },
        { label: 'Live Monitor', href: '/live' },
        { label: 'AI Oracle', href: '/oracle' },
        { label: 'Whale Tracker', href: '/whales' },
        { label: 'Trap Detector', href: '/traps' },
        { label: 'Arbitrage Hub', href: '/arbitrage' },
        { label: 'Strategy Forge', href: '/strategy' },
        { label: 'Alpha News', href: '/news' },
        { label: 'Seasonality', href: '/seasonality' },
        { label: 'Sector Analysis', href: '/sectors' },
        { label: 'Performance Audit', href: '/audit' },
        { label: 'Simulation Room', href: '/simulation' },
        { label: 'System Status', href: '/status' },
        { label: 'Portfolio', href: '/portfolio' },
        { label: 'Settings', href: '/settings' },
    ];

    test('should navigate through all primary routes', async ({ page }) => {
        // Increase timeout for slow dev server cold start and JIT compilation
        test.setTimeout(240000); // 4 minutes

        console.log('Navigating to base URL...');
        await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 90000 });
        console.log('Waiting for shell to become interactive...');
        await waitForShellReady(page);

        for (const route of routes) {
            console.log(`Verifying route: ${route.label} (${route.href})`);

            const currentPath = new URL(page.url()).pathname.replace(/\/$/, '') || '/';
            const targetPath = route.href.replace(/\/$/, '') || '/';
            if (currentPath !== targetPath) {
                const link = page.locator(`a[href="${route.href}"]`).first();
                const hasLink = await link.count().then((count) => count > 0);
                const canClickLink = hasLink && await link.isVisible().catch(() => false);

                if (canClickLink) {
                    console.log(`Clicking: ${route.label}`);
                    await link.click();
                } else {
                    console.log(`Direct navigation: ${route.label}`);
                    await page.goto(route.href, { waitUntil: 'domcontentloaded', timeout: 45000 });
                }
            }

            // Wait for URL transition - use a glob/regex that handles potential trailing slashes
            const urlPattern = new RegExp(`${route.href.replace(/\/$/, '')}/?$`);
            await expect(page).toHaveURL(urlPattern, { timeout: 45000 });
            await expect(page.getByRole('main')).toBeVisible({ timeout: 45000 });

            // Basic page load sanity check
            const bodyText = await page.innerText('body');
            const lowerBody = bodyText.toLowerCase();
            expect(lowerBody).not.toContain('page not found');
            expect(lowerBody).not.toMatch(/\b404\b/);

            console.log(`Route verified: ${route.label}`);
        }
    });

    test('should verify no major console errors on boot', async ({ page }) => {
        const errors = collectFatalConsoleErrors(page);

        await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 90000 });
        await waitForShellReady(page);

        await expect(page.getByRole('main')).toBeVisible({ timeout: 120000 });

        expect(errors).toHaveLength(0);
    });
});
