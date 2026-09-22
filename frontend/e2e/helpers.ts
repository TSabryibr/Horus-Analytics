import { expect, Page } from '@playwright/test';

const LEGACY_BOOT_STORAGE_KEY = 'horus_booted';
const SYSTEM_BOOT_SESSION_KEY = 'horus_booted_session';
const BOOT_ENTRY_LABEL = /enter (system|degraded)|skip sequence/i;

export async function primeHorusBoot(page: Page): Promise<void> {
  await page.addInitScript(
    ({ legacyKey, sessionKey }) => {
    try {
        localStorage.setItem(legacyKey, 'true');
        sessionStorage.setItem(sessionKey, 'true');
    } catch {
      // no-op
    }
    },
    {
      legacyKey: LEGACY_BOOT_STORAGE_KEY,
      sessionKey: SYSTEM_BOOT_SESSION_KEY,
    }
  );
}

export async function dismissBootSequence(page: Page): Promise<void> {
  const entryButton = page.getByRole('button', { name: BOOT_ENTRY_LABEL }).first();
  if (await entryButton.isVisible().catch(() => false)) {
    await entryButton.click({ force: true, timeout: 5000 }).catch(() => null);
    await expect(entryButton).toBeHidden({ timeout: 10000 }).catch(() => null);
  }
}

export async function waitForShellReady(page: Page): Promise<void> {
  await page.waitForLoadState('domcontentloaded');
  await dismissBootSequence(page);
  await expect(page.getByRole('main').first()).toBeVisible({ timeout: 45000 });
  const ribbon = page.getByTestId('command-ribbon-grid');
  await expect(ribbon).toBeVisible({ timeout: 45000 });
  await expect(ribbon.locator('a[href="/"]').first()).toBeVisible({ timeout: 45000 });
}

export function collectFatalConsoleErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() !== 'error') return;
    const text = msg.text();
    if (text.includes('Failed to fetch')) return;
    if (text.includes('ERR_CONNECTION_REFUSED')) return;
    if (text.includes('ERR_NETWORK_CHANGED')) return;
    if (text.includes('Failed to load resource: the server responded with a status of')) return;
    if (text.includes('fetch')) return;
    if (text.includes('WebSocket error') || text.includes('Live WS error')) return;
    errors.push(text);
  });
  return errors;
}
