import { AuditLog, Strategy } from '@/types/domain';

export function buildComparisonData(strategies: Strategy[] = []) {
    if (!strategies.length) return [];

    const maxLength = Math.max(...strategies.map((strategy) => strategy.equity_curve?.length || 0));
    const data = [];

    for (let index = 0; index < maxLength; index++) {
        const entry: Record<string, unknown> = { name: index };

        strategies.forEach((strategy) => {
            const point = strategy.equity_curve?.[index];
            if (point === undefined) return;
            entry[strategy.name] = typeof point === 'number' ? point : point?.value;
        });

        data.push(entry);
    }

    return data;
}

export function buildAuditCsvRows(logs: AuditLog[] = []) {
    const headers = ['Date', 'Ticker', 'Strategy', 'Entry Price', '1D Ret', '3D Ret', '5D Ret', 'Converted'];
    const rows = logs.map((log) => [
        log.date,
        log.ticker,
        log.strategy,
        log.entry_price,
        log.pnl_history?.['1D'] ?? '',
        log.pnl_history?.['3D'] ?? '',
        log.pnl_history?.['5D'] ?? '',
        log.converted ? 'YES' : 'NO',
    ]);

    return [headers, ...rows];
}

export function mergeAuditLog(logs: AuditLog[] = [], newLog: AuditLog, limit = 500) {
    const exists = logs.some((log) => {
        if (log.id && newLog.id) {
            return log.id === newLog.id;
        }

        return (
            log.timestamp === newLog.timestamp &&
            log.ticker === newLog.ticker &&
            log.strategy === newLog.strategy &&
            log.action === newLog.action
        );
    });

    if (exists) {
        return logs;
    }

    return [newLog, ...logs].slice(0, limit);
}
