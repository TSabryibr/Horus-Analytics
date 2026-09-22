import { test, expect, type Locator, type Page } from '@playwright/test';

import { primeHorusBoot, waitForShellReady } from './helpers';

const PRIMARY_ROUTES = [
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

async function assertActionable(locator: Locator, label: string): Promise<void> {
  await expect(locator, `${label} should be visible`).toBeVisible({ timeout: 45000 });
  await expect(locator, `${label} should be enabled`).toBeEnabled();
  await locator.click({ trial: true, timeout: 5000 });
}

async function assertRouteShell(page: Page, route: { label: string; href: string }) {
  await page.goto(route.href, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await waitForShellReady(page);
  await expect(page).toHaveURL(new RegExp(`${route.href.replace(/\/$/, '')}/?$`), { timeout: 45000 });
  await expect(page.getByRole('main').first()).toBeVisible({ timeout: 45000 });
  await expect(page.getByTestId('command-ribbon-grid')).toBeVisible({ timeout: 45000 });
  await assertActionable(page.getByRole('link', { name: /Terminal Dashboard/i }).first(), `${route.label} home nav`);
  await assertActionable(page.getByRole('link', { name: /Telegram Rail|Release Rail|nav.telegram/i }).first(), `${route.label} release rail nav`);
  await assertActionable(page.getByRole('button', { name: /Open portfolio command deck/i }), `${route.label} portfolio deck`);
  await assertActionable(page.getByRole('link', { name: /Open system status/i }), `${route.label} system status`);
}

test.describe('Horus interactive control audit', () => {
  test.beforeEach(async ({ page }) => {
    await primeHorusBoot(page);
  });

  test('stable shell controls are actionable across primary routes', async ({ page }) => {
    test.setTimeout(420000);

    for (const route of PRIMARY_ROUTES) {
      await assertRouteShell(page, route);
    }
  });

  test('expanded navigation menu items remain clickable without pointer interception', async ({ page }) => {
    await page.goto('/whales', { waitUntil: 'domcontentloaded', timeout: 90000 });
    await waitForShellReady(page);

    await page.getByRole('button', { name: /System navigation group/i }).click();
    await expect(page.getByRole('menu', { name: /System routes/i })).toBeVisible({ timeout: 10000 });
    const settingsItem = page.getByRole('menuitem', { name: /Settings/i }).first();
    await assertActionable(settingsItem, 'settings menu item');

    await page.getByRole('button', { name: /Oversight navigation group/i }).click();
    await expect(page.getByRole('menu', { name: /Oversight routes/i })).toBeVisible({ timeout: 10000 });
    const auditItem = page.getByRole('menuitem', { name: /Performance Audit|Audit/i }).first();
    await assertActionable(auditItem, 'oversight menu item');

    await page.getByRole('button', { name: /Intelligence navigation group/i }).click();
    await expect(page.getByRole('menu', { name: /Intelligence routes/i })).toBeVisible({ timeout: 10000 });
    const scannerItem = page.getByRole('menuitem', { name: /Market Scanner|Scanner/i }).first();
    await assertActionable(scannerItem, 'intelligence menu item');
  });
});
