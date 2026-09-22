import { fireEvent, render, screen } from '@testing-library/react';

import { AuditShell } from './AuditShell';

describe('AuditShell', () => {
    it('renders the header controls and delegates actions', () => {
        const setDays = jest.fn();
        const fetchData = jest.fn();
        const handleExport = jest.fn();

        render(
            <AuditShell
                days="ALL"
                setDays={setDays}
                fetchData={fetchData}
                handleExport={handleExport}
                loading={false}
                wsConnected={true}
                lastUpdated={new Date()}
            >
                <div>Audit body</div>
            </AuditShell>
        );

        expect(screen.getByText('Audit Trail')).toBeInTheDocument();
        expect(screen.getByText('⚡ WS LIVE')).toBeInTheDocument();
        expect(screen.getByText('Audit body')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '30D' }));
        fireEvent.click(screen.getByRole('button', { name: /Export Log/i }));
        fireEvent.click(screen.getByRole('button', { name: /Refresh audit data/i }));

        expect(setDays).toHaveBeenCalledWith(30);
        expect(handleExport).toHaveBeenCalledTimes(1);
        expect(fetchData).toHaveBeenCalledTimes(1);
    });

    it('shows the loading state instead of the body when loading', () => {
        render(
            <AuditShell
                days={7}
                setDays={jest.fn()}
                fetchData={jest.fn()}
                handleExport={jest.fn()}
                loading
                wsConnected={true}
                lastUpdated={null}
            >
                <div>Hidden audit body</div>
            </AuditShell>
        );

        expect(screen.getByText(/Consulting the ravens/i)).toBeInTheDocument();
        expect(screen.queryByText('Hidden audit body')).not.toBeInTheDocument();
    });

    it('shows LIVE indicator when connected and recently updated', () => {
        render(
            <AuditShell
                days="ALL"
                setDays={jest.fn()}
                fetchData={jest.fn()}
                handleExport={jest.fn()}
                loading={false}
                wsConnected={true}
                lastUpdated={new Date()}
            >
                <div>Audit body</div>
            </AuditShell>
        );

        expect(screen.getByText('LIVE')).toBeInTheDocument();
    });

    it('shows STREAM OFFLINE indicator when WebSocket disconnected', () => {
        render(
            <AuditShell
                days="ALL"
                setDays={jest.fn()}
                fetchData={jest.fn()}
                handleExport={jest.fn()}
                loading={false}
                wsConnected={false}
                lastUpdated={new Date()}
            >
                <div>Audit body</div>
            </AuditShell>
        );

        expect(screen.getByText('LIVE STREAM OFFLINE')).toBeInTheDocument();
    });

    it('shows stale indicator when data is older than 5 minutes', () => {
        const fiveMinutesAgo = new Date(Date.now() - 6 * 60 * 1000);
        render(
            <AuditShell
                days="ALL"
                setDays={jest.fn()}
                fetchData={jest.fn()}
                handleExport={jest.fn()}
                loading={false}
                wsConnected={true}
                lastUpdated={fiveMinutesAgo}
            >
                <div>Audit body</div>
            </AuditShell>
        );

        expect(screen.getByText('DATA MAY BE STALE')).toBeInTheDocument();
    });
});
