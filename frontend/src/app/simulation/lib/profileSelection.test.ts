import { normalizeSimulationProfiles } from './profileSelection';

describe('normalizeSimulationProfiles', () => {
    it('maps API profile_id payloads into UI ids', () => {
        const profiles = normalizeSimulationProfiles([
            {
                profile_id: 17,
                profile_name: 'EGX Price Action Pack - Higher High Higher Low',
                source_type: 'PRICE_ACTION',
                profile_state: 'READY',
                market: 'EGX30',
                timeframe: '1D',
            },
        ]);

        expect(profiles).toEqual([
            {
                id: 17,
                profile_name: 'EGX Price Action Pack - Higher High Higher Low',
                source_type: 'PRICE_ACTION',
                profile_state: 'READY',
                market: 'EGX30',
                timeframe: '1D',
            },
        ]);
    });

    it('keeps existing id payloads intact', () => {
        const profiles = normalizeSimulationProfiles([
            {
                id: 9,
                profile_name: 'Native Pine Profile',
                source_type: 'PINE',
            },
        ]);

        expect(profiles[0]?.id).toBe(9);
        expect(profiles[0]?.profile_name).toBe('Native Pine Profile');
    });
});
