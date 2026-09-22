import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { ManagementReport, ManagedHoldingForm } from '../hooks/usePortfolioManagement';
import { PortfolioManagementModal } from './PortfolioManagementModal';

describe('PortfolioManagementModal', () => {
    const holdings: ManagedHoldingForm[] = [
        {
            id: 1,
            ticker: 'COMI',
            shares: '100',
            entry_price: '90',
            total_cost: '',
            stop_loss: '80',
            target_price: '110',
            target_price_2: '120',
            currency: 'EGP',
            sector: 'Banking',
            notes: 'Core',
        },
    ];

    const report: ManagementReport = {
        portfolio: { id: 1, name: 'Main', type: 'USER', cash_egp: 10, cash_usd: 0 },
        snapshot_at: '2026-03-17T00:00:00Z',
        summary: {
            open_positions: 1,
            winners: 1,
            losers: 0,
            total_cost_basis: 100,
            market_value: 110,
            unrealized_pnl: 10,
            unrealized_pnl_pct: 10,
            action_items: 1,
        },
        risk: {
            status: 'SAFE',
            health_score: 91,
            heat: 12,
            recommendations: [],
        },
        positions: [],
        action_items: [
            {
                ticker: 'COMI',
                shares: 100,
                entry_price: 90,
                current_price: 100,
                stop_loss: 80,
                target_price: 110,
                target_price_2: 120,
                unrealized_pnl: 10,
                unrealized_pnl_pct: 10,
                action: 'HOLD',
                action_reason: 'Trend intact',
            },
        ],
    };

    it('renders management content and wires control callbacks', () => {
        const onClose = jest.fn();
        const onAddHolding = jest.fn();
        const onRemoveHolding = jest.fn();
        const onUpdateHolding = jest.fn();
        const onClearRows = jest.fn();
        const onRunIntake = jest.fn();
        const onUploadFile = jest.fn();
        const onDownloadTemplate = jest.fn();
        const onGenerateReport = jest.fn();
        const onSendReport = jest.fn();
        const onSetReportControls = jest.fn();

        render(
            <PortfolioManagementModal
                open
                managementLoading={false}
                managementMessage="Portfolio management report generated."
                managementReport={report}
                managementSendResult={{ status: 'sent', chunks_total: 2, chunks_sent: 2, chunks_failed: 0 }}
                managedHoldings={holdings}
                reportControls={{ include_positions: '15', chat_id: '', refresh_prices: true }}
                actionItemsPreviewLimit={15}
                onClose={onClose}
                onAddHolding={onAddHolding}
                onRemoveHolding={onRemoveHolding}
                onUpdateHolding={onUpdateHolding}
                onClearRows={onClearRows}
                onRunIntake={onRunIntake}
                onUploadFile={onUploadFile}
                onDownloadTemplate={onDownloadTemplate}
                onGenerateReport={onGenerateReport}
                onSendReport={onSendReport}
                onSetReportControls={onSetReportControls}
                truncatePrice={(value) => String(value)}
            />
        );

        expect(screen.getByRole('dialog', { name: /Portfolio management service/i })).toBeInTheDocument();
        expect(screen.getByText(/Portfolio management report generated./i)).toBeInTheDocument();
        expect(screen.getByText(/Action Items/i)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Download Template/i }));
        expect(onDownloadTemplate).toHaveBeenCalledWith('xlsx');

        fireEvent.click(screen.getByRole('button', { name: /Add Holding/i }));
        fireEvent.change(screen.getByDisplayValue('COMI'), { target: { value: 'HRHO' } });
        fireEvent.click(screen.getByRole('button', { name: /Run Intake/i }));
        fireEvent.click(screen.getByRole('button', { name: /Generate Report/i }));
        fireEvent.click(screen.getByRole('button', { name: /Send To Telegram/i }));
        fireEvent.click(screen.getByRole('button', { name: /Clear Rows/i }));
        fireEvent.click(screen.getByRole('button', { name: /Close/i }));

        expect(onAddHolding).toHaveBeenCalled();
        expect(onUpdateHolding).toHaveBeenCalledWith(1, 'ticker', 'HRHO');
        expect(onRunIntake).toHaveBeenCalled();
        expect(onGenerateReport).toHaveBeenCalled();
        expect(onSendReport).toHaveBeenCalled();
        expect(onClearRows).toHaveBeenCalled();
        expect(onClose).toHaveBeenCalled();

        fireEvent.change(screen.getByDisplayValue('15'), { target: { value: '20' } });
        expect(onSetReportControls).toHaveBeenCalledWith({ include_positions: '20', chat_id: '', refresh_prices: true });
    });

    it('supports destination mode switching and subscriber file upload', () => {
        const onUploadFile = jest.fn();

        render(
            <PortfolioManagementModal
                open
                managementLoading={false}
                managementMessage=""
                managementReport={null}
                managementSendResult={null}
                managedHoldings={[]}
                reportControls={{ include_positions: '15', chat_id: '', refresh_prices: true }}
                actionItemsPreviewLimit={15}
                onClose={jest.fn()}
                onAddHolding={jest.fn()}
                onRemoveHolding={jest.fn()}
                onUpdateHolding={jest.fn()}
                onClearRows={jest.fn()}
                onRunIntake={jest.fn()}
                onUploadFile={onUploadFile}
                onDownloadTemplate={jest.fn()}
                onGenerateReport={jest.fn()}
                onSendReport={jest.fn()}
                onSetReportControls={jest.fn()}
                truncatePrice={(value) => String(value)}
            />
        );

        // Default mode is create_new
        expect(screen.getByText(/Create New Client Book/i)).toBeInTheDocument();
        expect(screen.getByText(/Sandbox Audit/i)).toBeInTheDocument();
        expect(screen.getByText(/Overwrite Active Book/i)).toBeInTheDocument();

        // Switch to Sandbox mode
        fireEvent.click(screen.getByRole('button', { name: /Sandbox Audit/i }));
        expect(screen.getByText(/Sandbox Audit/i)).toBeInTheDocument();

        // Switch back to create_new and enter client name
        fireEvent.click(screen.getByRole('button', { name: /Create New Client Book/i }));
        const nameInput = screen.getByPlaceholderText(/Subscriber - Karim Mansour/i);
        fireEvent.change(nameInput, { target: { value: 'Client - Karim' } });

        const cashInput = screen.getByPlaceholderText(/50,000/i);
        fireEvent.change(cashInput, { target: { value: '75,000' } });

        // Drop file
        const dropzone = screen.getByText(/Drop Subscriber Excel/i);
        const testFile = new File(['Ticker,Shares\nCOMI,500'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        fireEvent.drop(dropzone, {
            dataTransfer: { files: [testFile] },
        });

        expect(onUploadFile).toHaveBeenCalledWith(testFile, {
            mode: 'create_new',
            portfolioName: 'Client - Karim',
            cashEgp: 75000,
        });
    });
});
