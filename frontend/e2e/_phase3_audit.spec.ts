import { test } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { dismissBootSequence, primeHorusBoot } from './helpers';

type ViewportSpec = {
  name: 'desktop' | 'mobile';
  width: number;
  height: number;
};

type LayoutIssue = {
  kind: 'horizontal-overflow' | 'missing-main' | 'collapsed-main';
  detail: string;
};

const routes = [
  '/',
  '/analytics',
  '/scanner',
  '/optimization',
  '/telegram',
  '/settings',
  '/live',
  '/status',
  '/sectors',
  '/arbitrage',
  '/audit',
  '/news',
  '/oracle',
  '/strategy',
  '/simulation',
  '/seasonality',
  '/traps',
  '/whales',
  '/portfolio'
];

const viewports: ViewportSpec[] = [
  { name: 'desktop', width: 1536, height: 960 },
  { name: 'mobile', width: 390, height: 844 }
];

const rootDir = path.resolve(__dirname, '..');
const outputDir = path.join(rootDir, '.qa', 'phase3');

async function collectLayoutIssues(page: import('@playwright/test').Page): Promise<LayoutIssue[]> {
  return page.evaluate(() => {
    const issues: LayoutIssue[] = [];
    const viewportWidth = window.innerWidth;
    const doc = document.documentElement;
    const horizontalOverflow = doc.scrollWidth - viewportWidth;

    if (horizontalOverflow > 4) {
      issues.push({
        kind: 'horizontal-overflow',
        detail: `document scroll width ${doc.scrollWidth}px exceeds viewport ${viewportWidth}px by ${horizontalOverflow}px`,
      });
    }

    const main = document.querySelector('main');
    if (!main) {
      issues.push({
        kind: 'missing-main',
        detail: 'No visible <main> landmark was rendered for the route',
      });
      return issues;
    }

    const rect = main.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) {
      issues.push({
        kind: 'collapsed-main',
        detail: `main rendered with bounding box ${Math.round(rect.width)}x${Math.round(rect.height)}`,
      });
    }

    return issues;
  });
}

test('phase 3 visual + runtime audit', async ({ browser, baseURL }) => {
  test.setTimeout(600000);
  if (!baseURL) {
    throw new Error('baseURL is not configured');
  }

  mkdirSync(outputDir, { recursive: true });
  const summary: Array<{
    route: string;
    viewport: string;
    pageErrors: string[];
    consoleErrors: string[];
    badResponses: Array<{ status: number; url: string }>;
    layoutIssues: LayoutIssue[];
    screenshot: string;
  }> = [];

  for (const viewport of viewports) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height }
    });

    for (const route of routes) {
      const page = await context.newPage();
      await primeHorusBoot(page);
      const pageErrors: string[] = [];
      const consoleErrors: string[] = [];
      const badResponses: Array<{ status: number; url: string }> = [];

      const onPageError = (error: Error) => {
        pageErrors.push(error.message);
      };
      const onConsole = (msg: { type: () => string; text: () => string }) => {
        if (msg.type() === 'error') {
          const text = msg.text();
          // Ignore transient fetch noise during rapid route transitions.
          if (text.includes('Failed to fetch')) return;
          // Ignore expected backend-offline noise in frontend-only runs.
          if (text.includes('ERR_CONNECTION_REFUSED')) return;
          if (text.includes('ERR_NETWORK_CHANGED')) return;
          // Treat response tracking as the source of truth for concrete missing assets.
          if (text.includes('Failed to load resource: the server responded with a status of 404')) return;
          consoleErrors.push(text);
        }
      };
      const onResponse = (resp: { status: () => number; url: () => string }) => {
        if (resp.status() >= 400) {
          const url = resp.url();
          // Ignore expected API 4xx/5xx noise from optional backend endpoints.
          if (!url.includes('/api/')) {
            badResponses.push({ status: resp.status(), url });
          }
        }
      };

      page.on('pageerror', onPageError);
      page.on('console', onConsole);
      page.on('response', onResponse);

      await page.goto(`${baseURL}${route}`, { waitUntil: 'domcontentloaded' });
      await dismissBootSequence(page);
      await page.getByRole('main').waitFor({ state: 'visible', timeout: 45000 });
      // Stabilize hydration before capture and avoid Playwright caret style mutation.
      await page.waitForLoadState('networkidle', { timeout: 2000 }).catch(() => null);
      await page.evaluate(() => {
        const active = document.activeElement;
        if (active instanceof HTMLElement) active.blur();
      }).catch(() => null);
      await page.waitForTimeout(500);
      const layoutIssues = await collectLayoutIssues(page);

      const safeRoute = route === '/' ? 'home' : route.replace(/\//g, '_').replace(/^_/, '');
      const screenshotFile = `${viewport.name}_${safeRoute}.png`;
      const screenshotPath = path.join(outputDir, screenshotFile);
      const screenshot = await page.screenshot({ fullPage: true, caret: 'initial' });
      writeFileSync(screenshotPath, screenshot);

      summary.push({
        route,
        viewport: viewport.name,
        pageErrors,
        consoleErrors,
        badResponses,
        layoutIssues,
        screenshot: `.qa/phase3/${screenshotFile}`
      });

      page.off('pageerror', onPageError);
      page.off('console', onConsole);
      page.off('response', onResponse);
      await page.close();
    }

    await context.close();
  }

  writeFileSync(path.join(outputDir, 'report.json'), JSON.stringify(summary, null, 2), 'utf-8');

  const failures = summary.filter(
    (entry) =>
      entry.pageErrors.length > 0 ||
      entry.consoleErrors.length > 0 ||
      entry.badResponses.length > 0 ||
      entry.layoutIssues.length > 0
  );

  if (failures.length > 0) {
    throw new Error(`Frontend audit found ${failures.length} route/viewport issues:\n${JSON.stringify(failures, null, 2)}`);
  }
});
