import { render, screen } from '@testing-library/react';

import { SentimentTimeline } from './SentimentTimeline';

describe('SentimentTimeline', () => {
    it('normalizes placeholder sentiment labels and reads gossip scores from asset news hits', () => {
        render(
            <SentimentTimeline
                score={50}
                regime="BORING MORTALS"
                hits={[
                    {
                        title: 'COMI expands digital banking footprint',
                        source: 'MUBASHER',
                        gossip_score: 4,
                    } as any,
                ]}
            />
        );

        expect(screen.getByText('NEUTRAL')).toBeInTheDocument();
        expect(screen.getByText('SCORE: +4')).toBeInTheDocument();
        expect(screen.getByText('MUBASHER')).toBeInTheDocument();
    });

    it('renders split scope and lead-ticker narrative sections in scope mode', () => {
        render(
            <SentimentTimeline
                score={58}
                regime="NEUTRAL"
                mode="scope"
                leadTicker="COMI"
                hits={[
                    {
                        title: 'Banking breadth improves across EGX70',
                        source: 'MUBASHER',
                        gossip_score: 3,
                    } as any,
                ]}
                leadHits={[
                    {
                        title: 'COMI expands corporate lending desk',
                        source: 'ENTERPRISE',
                        gossip_score: 5,
                    } as any,
                ]}
            />
        );

        expect(screen.getByText('Scope Narrative')).toBeInTheDocument();
        expect(screen.getByText('Lead Ticker Focus :: COMI')).toBeInTheDocument();
        expect(screen.getByText('Banking breadth improves across EGX70')).toBeInTheDocument();
        expect(screen.getByText('COMI expands corporate lending desk')).toBeInTheDocument();
    });

    it('labels neutral single-ticker narrative gaps with the ticker name', () => {
        render(
            <SentimentTimeline
                score={50}
                regime="NEUTRAL"
                ticker="ACAP"
                hits={[]}
            />
        );

        expect(screen.getByText('ACAP NEWS INDEX')).toBeInTheDocument();
        expect(screen.getByText('No ACAP-specific narrative hits detected.')).toBeInTheDocument();
    });
});
