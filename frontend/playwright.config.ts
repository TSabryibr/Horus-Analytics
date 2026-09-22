import * as os from 'node:os';
import * as path from 'node:path';
import { defineConfig, devices } from '@playwright/test';

const e2eDbFile = process.env.HORUS_E2E_DB_FILE
    || path.join(os.tmpdir(), `horus-e2e-${process.pid}.db`);

export default defineConfig({
    testDir: './e2e',
    testIgnore: ['**/_phase3_audit.spec.ts'],
    fullyParallel: true,
    timeout: 60 * 1000,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: 1,
    reporter: process.env.CI
        ? [['dot'], ['html', { open: 'never' }], ['github']]
        : 'html',
    use: {
        baseURL: 'http://127.0.0.1:3100',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        navigationTimeout: 60 * 1000,
    },
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],
    webServer: [
        {
            name: 'horus-api',
            command: 'python api.py',
            cwd: '..',
            url: 'http://127.0.0.1:8100/api/v1/health',
            reuseExistingServer: false,
            timeout: 180 * 1000,
            stdout: 'ignore',
            stderr: 'pipe',
            env: {
                ...process.env,
                HOST: '127.0.0.1',
                PORT: '8100',
                FRONTEND_PORT: '3100',
                HORUS_DB_FILE: e2eDbFile,
                HORUS_DB_JOURNAL_MODE: 'delete',
                HORUS_DB_SYNCHRONOUS: 'off',
                HORUS_AUTH_MODE: 'disabled',
                HORUS_DISABLE_BROWSER_AUTO_OPEN: '1',
                HORUS_DISABLE_READINESS_GATE: '1',
                SKIP_STARTUP_SYNC: 'true',
                LOCAL_FEED_AUTO_SELECT_ON_STARTUP: '0',
                PIPELINE_SYNC_WORKER_MODE: 'off',
                LIVE_ARM_GUARD_ENABLED: '0',
            },
        },
        {
            name: 'horus-frontend',
            command: 'npm run dev',
            url: 'http://127.0.0.1:3100',
            reuseExistingServer: !process.env.CI,
            timeout: 120 * 1000,
            env: {
                ...process.env,
                NEXT_PUBLIC_API_URL: 'http://127.0.0.1:8100',
            },
        },
    ],
});
