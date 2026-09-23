import {
    countRotationDecisions,
    deriveRotationRow,
    filterRotationRows,
    sortRotationRows,
} from './rotationCommandBoard';

describe('rotationCommandBoard', () => {
    it('classifies a Leading row moving upward and right as Confirm', () => {
        const result = deriveRotationRow(
            {
                Sector: 'Banks',
                Status: 'LEADING',
                x: 1.25,
                y: 2.5,
                trail: [
                    { x: -0.4, y: 1.1 },
                    { x: 1.25, y: 2.5 },
                ],
                Velocity: 2.1,
            },
            { viewMode: 'sectors', sectorRows: [] },
        );

        expect(result.decisionState).toBe('CONFIRM');
        expect(result.trajectory.direction).toBe('UP_RIGHT');
    });

    it('classifies a Lagging stock moving upward and right as Reversal Watch only when its sector confirms', () => {
        const result = deriveRotationRow(
            {
                ticker: 'FWRY',
                Sector: 'IT , Media & Communication Services',
                Status: 'LAGGING',
                x: -0.4,
                y: -1.2,
                trail: [
                    { x: -2.1, y: -3.4 },
                    { x: -0.4, y: -1.2 },
                ],
                Velocity: 2.8,
            },
            {
                viewMode: 'stocks',
                sectorRows: [
                    {
                        Sector: ' it,   media & communication services ',
                        Status: 'IMPROVING',
                        x: 0.8,
                        y: -0.2,
                    },
                ],
            },
        );

        expect(result.decisionState).toBe('REVERSAL_WATCH');
    });

    it.each([
        ['IMPROVING', 1, -1, -1, -2, 'EMERGING'],
        ['WEAKENING', -1, 2, 1, 3, 'DEGRADING'],
        ['LEADING', -1, 1, 1, 2, 'DEGRADING'],
        ['LAGGING', -1, -2, 1, -1, 'AVOID'],
        ['LAGGING', 1, -1, -1, -2, 'MONITOR'],
    ])(
        'applies ordered sector classification for %s',
        (status, x, y, startX, startY, expected) => {
            const result = deriveRotationRow(
                {
                    Sector: 'Banks',
                    Status: status,
                    x,
                    y,
                    trail: [
                        { x: startX, y: startY },
                        { x, y },
                    ],
                },
                { viewMode: 'sectors', sectorRows: [] },
            );

            expect(result.decisionState).toBe(expected);
        },
    );

    it('fails closed to Monitor when sector confirmation is ambiguous', () => {
        const stock = {
            ticker: 'FWRY',
            Sector: 'Fintech',
            Status: 'LAGGING',
            x: -0.2,
            y: -0.5,
            trail: [{ x: -1.2, y: -1.5 }, { x: -0.2, y: -0.5 }],
        };
        const duplicateSectors = [
            { Sector: 'Fintech', Status: 'LEADING', x: 1, y: 1 },
            { Sector: ' fintech ', Status: 'IMPROVING', x: 1, y: -1 },
        ];

        const result = deriveRotationRow(stock, {
            viewMode: 'stocks',
            sectorRows: duplicateSectors,
        });

        expect(result.decisionState).toBe('MONITOR');
        expect(result.sectorAlignment).toBe('UNAVAILABLE');
    });

    it('keeps a row visible as Monitor when its trajectory is unavailable', () => {
        const result = deriveRotationRow(
            {
                Sector: 'Banks',
                Status: 'LEADING',
                x: 1.2,
                y: 2.4,
                trail: [{ x: 1.2, y: 2.4 }],
            },
            { viewMode: 'sectors', sectorRows: [] },
        );

        expect(result.decisionState).toBe('MONITOR');
        expect(result.trajectory.direction).toBe('UNAVAILABLE');
    });

    it('filters multiple decision states and reports counts from the unfiltered population', () => {
        const rows = [
            deriveRotationRow(
                {
                    Sector: 'Banks',
                    Status: 'LEADING',
                    x: 2,
                    y: 3,
                    trail: [{ x: 1, y: 2 }, { x: 2, y: 3 }],
                },
                { viewMode: 'sectors', sectorRows: [] },
            ),
            deriveRotationRow(
                {
                    Sector: 'Food',
                    Status: 'LAGGING',
                    x: -2,
                    y: -3,
                    trail: [{ x: -1, y: -2 }, { x: -2, y: -3 }],
                },
                { viewMode: 'sectors', sectorRows: [] },
            ),
            deriveRotationRow(
                {
                    Sector: 'Utilities',
                    Status: 'WEAKENING',
                    x: -1,
                    y: 2,
                    trail: [{ x: -1, y: 2 }],
                },
                { viewMode: 'sectors', sectorRows: [] },
            ),
        ];

        expect(filterRotationRows(rows, new Set(['CONFIRM', 'DEGRADING']))).toHaveLength(2);
        expect(countRotationDecisions(rows)).toEqual({
            CONFIRM: 1,
            EMERGING: 0,
            REVERSAL_WATCH: 0,
            MONITOR: 0,
            DEGRADING: 1,
            AVOID: 1,
        });
    });

    it('sorts Rotation Priority by state, velocity, and stable display name', () => {
        const rows = [
            { decisionState: 'EMERGING', displayName: 'A', Velocity: 9 },
            { decisionState: 'CONFIRM', displayName: 'Z', Velocity: 1 },
            { decisionState: 'AVOID', displayName: 'C', Velocity: 5 },
            { decisionState: 'CONFIRM', displayName: 'B', Velocity: 3 },
        ] as Array<ReturnType<typeof deriveRotationRow>>;

        expect(
            sortRotationRows(rows, { mode: 'ROTATION_PRIORITY', direction: 'DESC' })
                .map((row) => row.displayName),
        ).toEqual(['B', 'Z', 'A', 'C']);
    });
});
