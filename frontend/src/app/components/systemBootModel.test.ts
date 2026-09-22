import { resolveBootConsoleModel } from './systemBootModel';

describe('resolveBootConsoleModel', () => {
    it('marks the system ready when all critical checks are aligned', () => {
        const model = resolveBootConsoleModel({
            system_ready: true,
            message: 'System Operational',
            pipeline_state: 'FRESH',
            db_connected: true,
            freshness: { market_open: true },
            data_status: {
                status: 'OK',
                history: {
                    ok: true,
                    status: 'FRESH',
                    kpis: { symbol_count: 87 },
                },
                intraday: {
                    ok: true,
                    status: 'LIVE',
                    age_mins: 1,
                },
            },
            scheduler: {
                running: true,
                jobs: [{ id: 'sync' }, { id: 'scan' }],
            },
            telegram: {
                enabled: false,
                configured: false,
            },
            metrics: {
                total_signals: 912,
            },
            timestamp: '2026-03-31T08:15:00Z',
        });

        expect(model.consoleState).toBe('READY');
        expect(model.entryMode).toBe('ready');
        expect(model.progress).toBe(100);
        expect(model.summary).toContain('System Operational');
    });

    it('marks the system degraded when market data is delayed', () => {
        const model = resolveBootConsoleModel({
            system_ready: false,
            pipeline_state: 'STALE',
            db_connected: true,
            freshness: { market_open: true },
            data_status: {
                status: 'OK',
                history: {
                    ok: true,
                    status: 'FRESH',
                    kpis: { symbol_count: 91 },
                },
                intraday: {
                    ok: false,
                    status: 'STALE',
                    age_mins: 44,
                },
            },
            scheduler: {
                running: true,
                jobs: [{ id: 'sync' }],
            },
            telegram: {
                enabled: true,
                configured: true,
            },
        });

        expect(model.consoleState).toBe('DEGRADED');
        expect(model.entryMode).toBe('degraded');
        expect(model.primaryIssue).toContain('Intraday feed delayed');
    });

    it('marks the console offline when no payload is available and the fetch failed', () => {
        const model = resolveBootConsoleModel(null, 'Backend unreachable');

        expect(model.consoleState).toBe('OFFLINE');
        expect(model.entryMode).toBe('blocked');
        expect(model.summary).toContain('Backend unreachable');
    });

    it('treats a lightweight fresh boot payload as ready even without detailed data_status', () => {
        const model = resolveBootConsoleModel({
            system_ready: true,
            message: 'Pipeline warm and ready.',
            pipeline_state: 'FRESH',
            db_connected: true,
            stale_mode: false,
            freshness: {
                market_open: true,
            },
            scheduler: {
                running: true,
            },
            telegram: {
                enabled: false,
                configured: false,
            },
            timestamp: '2026-03-31T08:15:00Z',
        });

        expect(model.consoleState).toBe('READY');
        expect(model.entryMode).toBe('ready');
    });

    it('marks the system ready at 100% during off-hours when market is closed and history is aligned', () => {
        const model = resolveBootConsoleModel({
            system_ready: true,
            message: 'Market closed. Historical book aligned.',
            pipeline_state: 'FRESH',
            db_connected: true,
            stale_mode: false,
            freshness: {
                market_open: false,
                history_ok: true,
                history: {
                    ok: true,
                    kpis: { symbol_count: 242 },
                },
            },
            scheduler: {
                running: true,
                jobs: [{ id: 'sync' }],
            },
            telegram: {
                enabled: true,
                configured: true,
            },
            timestamp: '2026-09-03T08:43:28Z',
        });

        expect(model.consoleState).toBe('READY');
        expect(model.entryMode).toBe('ready');
        expect(model.progress).toBe(100);
        expect(model.headline).toBe('Off-Hours Desk Ready');
        expect(model.checks.find((c) => c.key === 'market')?.state).toBe('ready');
        expect(model.checks.find((c) => c.key === 'market')?.detail).toBe('Session closed, history aligned');
        expect(model.metrics.find((m) => m.label === 'History')?.value).toBe('242 symbols');
    });

    it('displays Aligned (T-1) when symbol count is not explicitly tracked but off-hours history is ok', () => {
        const model = resolveBootConsoleModel({
            system_ready: true,
            message: 'Historical data ready.',
            pipeline_state: 'FRESH',
            db_connected: true,
            stale_mode: false,
            freshness: {
                market_open: false,
                history_ok: true,
            },
            scheduler: {
                running: true,
            },
            telegram: {
                enabled: false,
            },
            timestamp: '2026-09-03T08:43:28Z',
        });

        expect(model.consoleState).toBe('READY');
        expect(model.progress).toBe(100);
        expect(model.metrics.find((m) => m.label === 'History')?.value).toBe('Aligned (T-1)');
    });
});
