import fs from 'node:fs';
import path from 'node:path';

const appDir = path.join(process.cwd(), 'src', 'app');

function readAppFile(...segments: string[]) {
    return fs.readFileSync(path.join(appDir, ...segments), 'utf8');
}

describe('route entry boundaries', () => {
    it('keeps top-level home and analytics page entry files as server components', () => {
        const homePage = readAppFile('page.tsx');
        const analyticsPage = readAppFile('analytics', 'page.tsx');

        expect(homePage.startsWith("'use client'")).toBe(false);
        expect(homePage.startsWith('"use client"')).toBe(false);
        expect(analyticsPage.startsWith("'use client'")).toBe(false);
        expect(analyticsPage.startsWith('"use client"')).toBe(false);
    });

    it('moves interactive home and analytics logic into dedicated client leaf modules', () => {
        const homeClientPage = readAppFile('HomeClientPage.tsx');
        const analyticsClientPage = readAppFile('analytics', 'AnalyticsClientPage.tsx');

        expect(homeClientPage.startsWith("'use client'")).toBe(true);
        expect(analyticsClientPage.startsWith("'use client'")).toBe(true);
    });
});
