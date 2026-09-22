import { test, expect, type Locator, type Page } from '@playwright/test';
import { primeHorusBoot, waitForShellReady, collectFatalConsoleErrors } from './helpers';

const PRIMARY_ROUTES = [
  { label: 'Terminal Dashboard', href: '/' },
  { label: 'Market Scanner', href: '/scanner' },
  { label: 'Live Monitor', href: '/live' },
  { label: 'AI Oracle', href: '/oracle' },
  { label: 'Whale Tracker', href: '/whales' },
  { label: 'Trap Detector', href: '/traps' },
  { label: 'Performance Audit', href: '/audit' },
  { label: 'Simulation Room', href: '/simulation' },
  { label: 'Portfolio', href: '/portfolio' },
];

async function expectActionable(locator: Locator, label: string) {
  await expect(locator, `${label} should be visible`).toBeVisible({ timeout: 45000 });
  await expect(locator, `${label} should be enabled`).toBeEnabled();
  await locator.click({ trial: true, timeout: 5000 });
}

async function expectShellControls(page: Page) {
  await expectActionable(page.getByRole('button', { name: /Open portfolio command deck/i }), 'portfolio command deck');
  await expectActionable(page.getByRole('link', { name: /Open system status/i }), 'system status link');
  await expectActionable(page.getByRole('button', { name: /Matrix Travel/i }), 'matrix travel');
  await expectActionable(page.getByRole('button', { name: /Toggle language/i }), 'language toggle');
  await expectActionable(page.getByRole('button', { name: /Intelligence navigation group/i }), 'intelligence nav group');
  await expectActionable(page.getByRole('button', { name: /Oversight navigation group/i }), 'oversight nav group');
  await expectActionable(page.getByRole('button', { name: /System navigation group/i }), 'system nav group');
}

test.describe('Horus comprehensive route interaction smoke', () => {
  let fatalErrors: string[] = [];

  test.beforeEach(async ({ page }) => {
    fatalErrors = collectFatalConsoleErrors(page);
    await primeHorusBoot(page);
  });

  test.afterEach(() => {
    expect(fatalErrors, `Fatal console errors detected:\n${fatalErrors.join('\n')}`).toHaveLength(0);
  });

  for (const route of PRIMARY_ROUTES) {
    test(`verifies stable controls on ${route.label} (${route.href})`, async ({ page }) => {
      await page.goto(route.href, { waitUntil: 'domcontentloaded', timeout: 90000 });
      await waitForShellReady(page);
      await expect(page).toHaveURL(new RegExp(`${route.href.replace(/\/$/, '')}/?$`), { timeout: 45000 });
      const main = page.getByRole('main').first();
      await expect(main).toBeVisible({ timeout: 45000 });
      await expectShellControls(page);

      const bodyText = await page.locator('body').innerText();
      expect(bodyText.toLowerCase()).not.toContain('page not found');
      expect(bodyText.toLowerCase()).not.toMatch(/\b404\b/);
      expect(bodyText.trim().length).toBeGreaterThan(20);
    });
  }
});
