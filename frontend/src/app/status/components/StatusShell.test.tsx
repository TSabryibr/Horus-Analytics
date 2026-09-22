import { fireEvent, render, screen } from '@testing-library/react';

import { StatusShell } from './StatusShell';

describe('StatusShell', () => {
    it('renders header chrome and delegates refresh behavior', () => {
        const fetchStatus = jest.fn();

        render(
            <StatusShell
                loading={false}
                lastRefresh={new Date('2026-03-18T12:00:00Z')}
                runtimeState={{
                    code: 'FRESH',
                    label: 'All Systems Go',
                    dotClass: 'bg-emerald-500',
                    textClass: 'text-emerald-400',
                }}
                fetchStatus={fetchStatus}
            >
                <div>Status body</div>
            </StatusShell>
        );

        expect(screen.getByRole('heading', { name: /Observability Terminal/i })).toBeInTheDocument();
        expect(screen.getByText('Runtime State')).toBeInTheDocument();
        expect(screen.getByText('All Systems Go')).toBeInTheDocument();
        expect(screen.getByText('Status body')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /FORCE RE-VALIDATION/i }));
        expect(fetchStatus).toHaveBeenCalledTimes(1);
    });

    it('keeps the shell visible while showing a loading banner', () => {
        render(
            <StatusShell
                loading
                lastRefresh={new Date('2026-03-18T12:00:00Z')}
                runtimeState={{
                    code: 'DETECTING',
                    label: 'Detecting Feed',
                    dotClass: 'bg-cyan-500',
                    textClass: 'text-cyan-400',
                }}
                fetchStatus={jest.fn()}
            >
                <div>Visible body</div>
            </StatusShell>
        );

        expect(screen.getByRole('heading', { name: /Observability Terminal/i })).toBeInTheDocument();
        expect(screen.getByText('Runtime State')).toBeInTheDocument();
        expect(screen.getByText('Visible body')).toBeInTheDocument();
        expect(screen.getByText(/Sampling live status feed/i)).toBeInTheDocument();
    });

    it('shows a stable placeholder until the first refresh timestamp is available', () => {
        render(
            <StatusShell
                loading={false}
                lastRefresh={null}
                runtimeState={{
                    code: 'DETECTING',
                    label: 'Detecting Feed',
                    dotClass: 'bg-cyan-500',
                    textClass: 'text-cyan-400',
                }}
                fetchStatus={jest.fn()}
            >
                <div>Status body</div>
            </StatusShell>
        );

        expect(screen.getByText('--:--:--')).toBeInTheDocument();
    });
});
