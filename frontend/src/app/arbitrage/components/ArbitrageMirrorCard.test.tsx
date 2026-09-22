import { render, screen, fireEvent } from '@testing-library/react';
import { ArbitrageMirrorCard } from './ArbitrageMirrorCard';

describe('ArbitrageMirrorCard', () => {
    const mockMirror = {
        Leader: 'COMI',
        Follower: 'HRHO',
        Lag: 2,
        Confidence: 81.2,
        Type: 'Positive',
        ZScore: 2.5,
    };

    const mockOnExecute = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders mirror details correctly', () => {
        render(
            <ArbitrageMirrorCard
                mirror={mockMirror}
                idx={0}
                isExecuting={false}
                actionStatus={null}
                onExecute={mockOnExecute}
            />
        );

        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument(); // Lag
        expect(screen.getByText('2.50')).toBeInTheDocument(); // ZScore
        expect(screen.getByText('81.2%')).toBeInTheDocument(); // Confidence
        expect(screen.getByText('Positive Echo')).toBeInTheDocument(); // Type
    });

    it('calls onExecute when execute button is clicked', () => {
        render(
            <ArbitrageMirrorCard
                mirror={mockMirror}
                idx={0}
                isExecuting={false}
                actionStatus={null}
                onExecute={mockOnExecute}
            />
        );

        const executeButton = screen.getByText('Execute Lead-Lag Trade');
        fireEvent.click(executeButton);

        expect(mockOnExecute).toHaveBeenCalledTimes(1);
        expect(mockOnExecute).toHaveBeenCalledWith(mockMirror, 0);
    });

    it('disables button and shows loading state when executing', () => {
        render(
            <ArbitrageMirrorCard
                mirror={mockMirror}
                idx={0}
                isExecuting={true}
                actionStatus={null}
                onExecute={mockOnExecute}
            />
        );

        const executeButton = screen.getByText('Routing Execution...');
        expect(executeButton).toBeDisabled();
        expect(executeButton.closest('button')?.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('displays action status message if id matches', () => {
        render(
            <ArbitrageMirrorCard
                mirror={mockMirror}
                idx={0}
                isExecuting={false}
                actionStatus={{ id: 0, msg: 'Execution successful', type: 'success' }}
                onExecute={mockOnExecute}
            />
        );

        expect(screen.getByText('Execution successful')).toBeInTheDocument();
        expect(screen.getByText('Execution successful')).toHaveClass('bg-emerald-900/40');
    });

    it('displays error action status message', () => {
        render(
            <ArbitrageMirrorCard
                mirror={mockMirror}
                idx={1}
                isExecuting={false}
                actionStatus={{ id: 1, msg: 'Execution failed', type: 'error' }}
                onExecute={mockOnExecute}
            />
        );

        expect(screen.getByText('Execution failed')).toBeInTheDocument();
        expect(screen.getByText('Execution failed')).toHaveClass('bg-red-900/40');
    });

    it('does not display action status message if id does not match', () => {
        render(
            <ArbitrageMirrorCard
                mirror={mockMirror}
                idx={0}
                isExecuting={false}
                actionStatus={{ id: 1, msg: 'Execution failed', type: 'error' }}
                onExecute={mockOnExecute}
            />
        );

        expect(screen.queryByText('Execution failed')).not.toBeInTheDocument();
    });
});
