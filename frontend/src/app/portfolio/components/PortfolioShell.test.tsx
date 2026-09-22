import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { PortfolioHealth, Position } from '@/types';
import { HoardData, PortfolioAnalysisReport, PortfolioReportBundle } from '../hooks/usePortfolioRuntime';
import { PortfolioShell } from './PortfolioShell';

jest.mock('@/components/PortfolioTable', () => ({
    PortfolioTable: ({ onClose }: { onClose: (ticker: string) => void }) => (
        <div data-testid="mock-portfolio-table">
            <button type="button" onClick={() => onClose('COMI')}>
                Close COMI
            </button>
        </div>
    ),
}));

jest.mock('./PortfolioReportSection', () => ({
    __esModule: true,
    default: () => <div data-testid="mock-portfolio-report-section" />,
}));

const hoard: HoardData = {
    status: 'active',
    net_worth_egp: 1500000,
    net_worth_usd: 10000,
    cash_egp: 250000,
    cash_usd: 1200,
    positions: [
        {
            id: 1,
            ticker: 'COMI',
            shares: 100,
            entry_price: 90,
            current_price: 100,
            pnl: 1000,
            pnl_pct: 11.11,
            status: 'OPEN',
        } as Position,
    ],
};

const health: PortfolioHealth = {
    status: 'success',
    diagnoses: [],
};

const analysis: PortfolioAnalysisReport = {
    status: 'success',
    health_score: 90,
    heat: 1,
    recommendations: [],
    sector_breakdown: {},
};

const report: PortfolioReportBundle = {
    metrics: { total_pnl: 300, win_rate: 50, profit_factor: 1.2, total_trades: 3 },
    curve: [{ date: 'Baseline', equity: 1000000 }],
    trades: [{ ticker: 'COMI', entry_price: 50, exit_price: 53, exit_date: '2026-03-17', pnl: 300 }],
};

describe('PortfolioShell', () => {
    it('renders initialized shell and wires toolbar actions', async () => {
        const importFileInputRef = { current: null } as React.RefObject<HTMLInputElement>;
        const reportingSectionRef = { current: null } as React.RefObject<HTMLDivElement>;
        const onRefresh = jest.fn();
        const onExport = jest.fn();
        const onTriggerImportPicker = jest.fn();
        const onOpenAddPosition = jest.fn();
        const onOpenManagement = jest.fn();
        const onOpenAnalysis = jest.fn();
        const onUpdateBalances = jest.fn();
        const onClosePosition = jest.fn();

        render(
            <PortfolioShell
                hoard={hoard}
                health={health}
                analysis={analysis}
                report={report}
                loading={false}
                uiMessage={{ type: 'success', text: 'Ready' }}
                importLoading={false}
                activePortfolioId={1}
                importFileInputRef={importFileInputRef}
                reportingSectionRef={reportingSectionRef}
                onImportCsv={jest.fn()}
                onRefresh={onRefresh}
                onExport={onExport}
                onTriggerImportPicker={onTriggerImportPicker}
                onOpenGenesis={jest.fn()}
                onUpdateBalances={onUpdateBalances}
                onOpenAddPosition={onOpenAddPosition}
                onOpenManagement={onOpenManagement}
                onOpenAnalysis={onOpenAnalysis}
                onEditPosition={jest.fn()}
                onClosePosition={onClosePosition}
            />
        );

        expect(screen.getByRole('heading', { name: /Portfolio Manager/i })).toBeInTheDocument();
        expect(screen.getByTestId('mock-portfolio-table')).toBeInTheDocument();
        expect(await screen.findByTestId('mock-portfolio-report-section')).toBeInTheDocument();
        expect(screen.getAllByText('Ready').length).toBeGreaterThan(0);

        fireEvent.click(screen.getByRole('button', { name: /Export CSV/i }));
        fireEvent.click(screen.getByRole('button', { name: /Import File/i }));
        fireEvent.click(screen.getByRole('button', { name: /Add Position/i }));
        fireEvent.click(screen.getByRole('button', { name: /Management Service/i }));
        fireEvent.click(screen.getByRole('button', { name: /Risk Score/i }));
        fireEvent.click(screen.getByRole('button', { name: /Update Balances/i }));
        fireEvent.click(screen.getByRole('button', { name: /Close COMI/i }));

        expect(onExport).toHaveBeenCalled();
        expect(onTriggerImportPicker).toHaveBeenCalled();
        expect(onOpenAddPosition).toHaveBeenCalled();
        expect(onOpenManagement).toHaveBeenCalled();
        expect(onOpenAnalysis).toHaveBeenCalled();
        expect(onUpdateBalances).toHaveBeenCalled();
        expect(onClosePosition).toHaveBeenCalledWith('COMI');
    });

    it('renders setup required view when hoard is not present and triggers genesis', () => {
        const importFileInputRef = { current: null } as React.RefObject<HTMLInputElement>;
        const reportingSectionRef = { current: null } as React.RefObject<HTMLDivElement>;
        const onRefresh = jest.fn();
        const onTriggerImportPicker = jest.fn();
        const onOpenGenesis = jest.fn();

        render(
            <PortfolioShell
                hoard={null}
                health={null}
                analysis={null}
                report={null}
                loading={false}
                uiMessage={{ type: 'error', text: 'Genesis required' }}
                importLoading={false}
                activePortfolioId={1}
                importFileInputRef={importFileInputRef}
                reportingSectionRef={reportingSectionRef}
                onImportCsv={jest.fn()}
                onRefresh={onRefresh}
                onExport={jest.fn()}
                onTriggerImportPicker={onTriggerImportPicker}
                onOpenGenesis={onOpenGenesis}
                onUpdateBalances={jest.fn()}
                onOpenAddPosition={jest.fn()}
                onOpenManagement={jest.fn()}
                onOpenAnalysis={jest.fn()}
                onEditPosition={jest.fn()}
                onClosePosition={jest.fn()}
                genesisModal={<div data-testid="mock-genesis-modal" />}
            />
        );

        expect(screen.getByText(/Portfolio Setup Required/i)).toBeInTheDocument();
        expect(screen.getByText('Genesis required')).toBeInTheDocument();
        expect(screen.getByTestId('mock-genesis-modal')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Initialize Treasury/i }));
        fireEvent.click(screen.getByRole('button', { name: /Import Subscriber File/i }));
        fireEvent.click(screen.getByRole('button', { name: /Refresh/i }));

        expect(onOpenGenesis).toHaveBeenCalled();
        expect(onTriggerImportPicker).toHaveBeenCalled();
        expect(onRefresh).toHaveBeenCalled();
    });

    it('skips the report section when no active portfolio id is available', () => {
        render(
            <PortfolioShell
                hoard={hoard}
                health={health}
                analysis={analysis}
                report={report}
                loading={false}
                uiMessage={null}
                importLoading={false}
                activePortfolioId={null}
                importFileInputRef={{ current: null } as React.RefObject<HTMLInputElement>}
                reportingSectionRef={{ current: null } as React.RefObject<HTMLDivElement>}
                onImportCsv={jest.fn()}
                onRefresh={jest.fn()}
                onExport={jest.fn()}
                onTriggerImportPicker={jest.fn()}
                onOpenGenesis={jest.fn()}
                onUpdateBalances={jest.fn()}
                onOpenAddPosition={jest.fn()}
                onOpenManagement={jest.fn()}
                onOpenAnalysis={jest.fn()}
                onEditPosition={jest.fn()}
                onClosePosition={jest.fn()}
            />
        );

        expect(screen.queryByTestId('mock-portfolio-report-section')).not.toBeInTheDocument();
    });

    it('renders system fleet portfolio with read-only indicators and replicate action', () => {
        const onReplicatePortfolio = jest.fn();

        render(
            <PortfolioShell
                hoard={hoard}
                health={health}
                analysis={analysis}
                report={report}
                loading={false}
                uiMessage={null}
                importLoading={false}
                activePortfolioId={8}
                isSystemPortfolio={true}
                importFileInputRef={{ current: null } as React.RefObject<HTMLInputElement>}
                reportingSectionRef={{ current: null } as React.RefObject<HTMLDivElement>}
                onImportCsv={jest.fn()}
                onRefresh={jest.fn()}
                onExport={jest.fn()}
                onTriggerImportPicker={jest.fn()}
                onOpenGenesis={jest.fn()}
                onUpdateBalances={jest.fn()}
                onOpenAddPosition={jest.fn()}
                onOpenManagement={jest.fn()}
                onOpenAnalysis={jest.fn()}
                onEditPosition={jest.fn()}
                onClosePosition={jest.fn()}
                onReplicatePortfolio={onReplicatePortfolio}
            />
        );

        expect(screen.getByText('System Fleet')).toBeInTheDocument();
        expect(screen.getByText('Simulation Benchmark')).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Add Position/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Import CSV/i })).not.toBeInTheDocument();

        const replicateBtn = screen.getByRole('button', { name: /Replicate Fleet/i });
        expect(replicateBtn).toBeInTheDocument();
        fireEvent.click(replicateBtn);
        expect(onReplicatePortfolio).toHaveBeenCalledWith(8);
    });
});
