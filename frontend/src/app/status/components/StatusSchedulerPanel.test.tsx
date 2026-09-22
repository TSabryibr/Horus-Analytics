import { render, screen } from '@testing-library/react';

import { StatusSchedulerPanel } from './StatusSchedulerPanel';

const jobs = [
    { id: 'scan-daily', trigger: 'cron', next_run: '09:00' },
    { id: 'monitor-live', trigger: 'interval', next_run: 'Asynchronous' },
];

describe('StatusSchedulerPanel', () => {
    it('renders scheduler jobs in the pipeline table', () => {
        render(<StatusSchedulerPanel jobs={jobs} />);

        expect(screen.getByText('Job Scheduler Pipeline')).toBeInTheDocument();
        expect(screen.getByText('scan-daily')).toBeInTheDocument();
        expect(screen.getByText('monitor-live')).toBeInTheDocument();
        expect(screen.getByText('cron')).toBeInTheDocument();
        expect(screen.getByText('Asynchronous')).toBeInTheDocument();
    });

    it('renders an empty-state row while the job list is unavailable', () => {
        render(<StatusSchedulerPanel jobs={[]} />);

        expect(screen.getByText('Job list refreshing')).toBeInTheDocument();
    });
});
