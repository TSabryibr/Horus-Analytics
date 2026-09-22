import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { WeeklyReportNotesPanel } from './WeeklyReportNotesPanel';

describe('WeeklyReportNotesPanel', () => {
    it('renders nothing when there are no warnings or notes', () => {
        const { container } = render(
            <WeeklyReportNotesPanel
                notes={[]}
                warnings={[]}
            />,
        );

        expect(container.firstChild).toBeNull();
    });

    it('renders warnings and notes when present', () => {
        render(
            <WeeklyReportNotesPanel
                notes={['Momentum leadership was concentrated in two sectors.']}
                warnings={['Signal sample size was low.']}
                />,
        );

        expect(screen.getByText('Report Notes')).toBeInTheDocument();
        expect(screen.getByText('- Signal sample size was low.')).toBeInTheDocument();
        expect(screen.getByText('- Momentum leadership was concentrated in two sectors.')).toBeInTheDocument();
    });

    it('shows overflow indicator when warnings exceed 8', async () => {
        const user = userEvent.setup();
        const warnings = Array.from({ length: 12 }, (_, i) => `Warning ${i + 1}`);
        render(
            <WeeklyReportNotesPanel
                notes={[]}
                warnings={warnings}
            />,
        );

        expect(screen.getByText('- Warning 1')).toBeInTheDocument();
        expect(screen.getByText('- Warning 8')).toBeInTheDocument();
        expect(screen.queryByText('- Warning 9')).not.toBeInTheDocument();
        expect(screen.getByText('+4 more warnings hidden')).toBeInTheDocument();

        await user.click(screen.getByText('+4 more warnings hidden'));

        expect(screen.getByText('- Warning 9')).toBeInTheDocument();
        expect(screen.getByText('- Warning 12')).toBeInTheDocument();
    });

    it('shows overflow indicator when notes exceed 8', async () => {
        const user = userEvent.setup();
        const notes = Array.from({ length: 10 }, (_, i) => `Note ${i + 1}`);
        render(
            <WeeklyReportNotesPanel
                notes={notes}
                warnings={[]}
            />,
        );

        expect(screen.getByText('+2 more notes hidden')).toBeInTheDocument();

        await user.click(screen.getByText('+2 more notes hidden'));

        expect(screen.getByText('- Note 9')).toBeInTheDocument();
        expect(screen.getByText('- Note 10')).toBeInTheDocument();
    });
});
