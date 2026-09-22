import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { OptimizerControlPanel } from './OptimizerControlPanel';

describe('OptimizerControlPanel', () => {
    it('forwards optimizer controls and result actions', () => {
        const setOptIndex = jest.fn();
        const onRunOptimizer = jest.fn();
        const onTestMatrix = jest.fn();

        render(
            <OptimizerControlPanel
                optIndex="ALL"
                setOptIndex={setOptIndex}
                optLoading={false}
                optimizerStatus="COMPLETED"
                optimizerIsActive={false}
                optimizerHasResults
                optStatus={{
                    status: 'COMPLETED',
                    progress: 100,
                    result: [
                        {
                            score: 91.5,
                            win_rate: 62.4,
                            avg_return: 8.1,
                            trades: 33,
                            params: {
                                RSI_MIN: 55,
                                RSI_MAX: 85,
                                VOL_SPIKE: 1.5,
                                SL_PCT: 1.5,
                                TP1_PCT: 4,
                                MOMENTUM: 2.5,
                            },
                        },
                    ],
                }}
                onRunOptimizer={onRunOptimizer}
                onTestMatrix={onTestMatrix}
            />
        );

        fireEvent.change(screen.getByLabelText(/Optimizer Index/i), { target: { value: 'EGX30' } });
        fireEvent.click(screen.getByRole('button', { name: /Execute_Optimization/i }));
        fireEvent.click(screen.getByRole('button', { name: /Test_Matrix/i }));

        expect(setOptIndex).toHaveBeenCalledWith('EGX30');
        expect(onRunOptimizer).toHaveBeenCalled();
        expect(onTestMatrix).toHaveBeenCalledWith(
            expect.objectContaining({
                RSI_MIN: 55,
                RSI_MAX: 85,
            })
        );
        expect(screen.getByText('Optimization_Log')).toBeInTheDocument();
        expect(screen.getByText('CONVERGED ⚡')).toBeInTheDocument();
    });
});
