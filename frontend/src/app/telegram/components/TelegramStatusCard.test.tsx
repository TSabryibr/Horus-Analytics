import React from 'react';
import { render, screen } from '@testing-library/react';

import { TelegramStatusCard } from './TelegramStatusCard';

describe('TelegramStatusCard', () => {
    it('renders online and offline channel states', () => {
        const { rerender } = render(
            <TelegramStatusCard
                configured
                operatingMode="AI_ASSIST"
                autopilotArmed
                autopilotStatus="READY"
                readyCount={3}
                failedDeliveryCount={2}
                pendingFollowUpCount={1}
                readyFollowUpCount={2}
                failedFollowUpCount={1}
            />
        );

        expect(screen.getByText('CHANNEL ONLINE')).toBeInTheDocument();
        expect(screen.getByText('AI_ASSIST')).toBeInTheDocument();
        expect(screen.getByText('3 ready')).toBeInTheDocument();
        expect(screen.getByText('3 queued updates')).toBeInTheDocument();
        expect(screen.getByText('Autopilot Armed')).toBeInTheDocument();
        expect(screen.getByText('Auto READY')).toBeInTheDocument();
        expect(screen.getByText('2 Retry Needed')).toBeInTheDocument();
        expect(screen.getByText('1 Update Failed')).toBeInTheDocument();

        rerender(<TelegramStatusCard configured={false} />);

        expect(screen.getByText('OFFLINE')).toBeInTheDocument();
    });
});
