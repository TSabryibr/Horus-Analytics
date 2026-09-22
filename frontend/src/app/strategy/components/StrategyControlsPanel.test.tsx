import { fireEvent, render, screen } from '@testing-library/react';

import { StrategyControlsPanel } from './StrategyControlsPanel';

describe('StrategyControlsPanel', () => {
    it('renders proposed changes and AI apply action', () => {
        const onApply = jest.fn();

        render(
            <StrategyControlsPanel
                applying={false}
                manualMode={false}
                manualParams={{ RSI_MIN: 58, RSI_MAX: 82, SL_PCT: 1.5, TP_PCT: 3 }}
                onApply={onApply}
                onManualParamChange={jest.fn()}
                proposal={{
                    changes: [
                        { parameter: 'RSI_MIN', old_value: 55, new_value: 58, changed: true },
                        { parameter: 'SL_PCT', old_value: 1.5, new_value: 1.5, changed: false },
                    ],
                }}
            />,
        );

        expect(screen.getByText('Proposed Laws (Parameters)')).toBeInTheDocument();
        expect(screen.getByText('RSI_MIN')).toBeInTheDocument();
        expect(screen.getByText('Apply Strategy Changes')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Apply Strategy Changes/i }));
        expect(onApply).toHaveBeenCalledTimes(1);
    });

    it('renders manual sliders and reports changes', () => {
        const onManualParamChange = jest.fn();

        render(
            <StrategyControlsPanel
                applying={false}
                manualMode
                manualParams={{ RSI_MIN: 58, RSI_MAX: 82, SL_PCT: 1.5, TP_PCT: 3 }}
                onApply={jest.fn()}
                onManualParamChange={onManualParamChange}
                proposal={{
                    changes: [],
                }}
            />,
        );

        expect(screen.getByText('Manual Overrides')).toBeInTheDocument();
        expect(screen.getByText('Apply Manual Overrides')).toBeInTheDocument();

        fireEvent.change(screen.getByDisplayValue('58'), { target: { value: '60' } });
        expect(onManualParamChange).toHaveBeenCalledWith('RSI_MIN', 60);
    });

    it('renders optimized state when no AI changes are present', () => {
        render(
            <StrategyControlsPanel
                applying={false}
                manualMode={false}
                manualParams={{ RSI_MIN: 58, RSI_MAX: 82, SL_PCT: 1.5, TP_PCT: 3 }}
                onApply={jest.fn()}
                onManualParamChange={jest.fn()}
                proposal={{
                    changes: [
                        { parameter: 'RSI_MIN', old_value: 55, new_value: 55, changed: false },
                    ],
                }}
            />,
        );

        expect(screen.getByText('System is already optimized')).toBeDisabled();
    });
});
