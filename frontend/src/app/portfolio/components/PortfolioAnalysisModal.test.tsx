import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { PortfolioAnalysisReport } from '../hooks/usePortfolioRuntime';
import { PortfolioAnalysisModal } from './PortfolioAnalysisModal';

describe('PortfolioAnalysisModal', () => {
    it('renders diagnostics content and closes through the header action', () => {
        const analysis: PortfolioAnalysisReport = {
            status: 'WARNING',
            health_score: 67,
            heat: 4,
            recommendations: [
                {
                    type: 'risk',
                    severity: 'HIGH',
                    title: 'Trim concentration',
                    message: 'Reduce oversized exposure.',
                },
            ],
            sector_breakdown: {
                Banking: 2,
                Energy: 1,
            },
        };
        const onClose = jest.fn();

        render(<PortfolioAnalysisModal analysis={analysis} onClose={onClose} />);

        expect(screen.getByRole('dialog', { name: /Portfolio diagnostics/i })).toBeInTheDocument();
        expect(screen.getByText(/67/)).toBeInTheDocument();
        expect(screen.getByText(/4%/)).toBeInTheDocument();
        expect(screen.getByText(/Trim concentration/i)).toBeInTheDocument();
        expect(screen.getByText('Banking')).toBeInTheDocument();
        expect(screen.getByText('Energy')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Close/i }));

        expect(onClose).toHaveBeenCalled();
    });

    it('renders the healthy empty-recommendations state', () => {
        const analysis: PortfolioAnalysisReport = {
            status: 'SAFE',
            health_score: 91,
            heat: 1,
            recommendations: [],
            sector_breakdown: {},
        };

        render(<PortfolioAnalysisModal analysis={analysis} onClose={jest.fn()} />);

        expect(screen.getByText(/No critical issues detected/i)).toBeInTheDocument();
        expect(screen.getByText(/No sector data available/i)).toBeInTheDocument();
    });
});
