import {
    buildRrgDomain,
    clipPointToDomain,
    getOutlierPin,
} from './rrgGeometry';
import type { DerivedRotationRow } from './rotationCommandBoard';

function row(displayName: string, x: number, y: number): DerivedRotationRow {
    return {
        Sector: displayName,
        Status: 'LEADING',
        x,
        y,
        trail: [{ x: x - 1, y: y - 1 }, { x, y }],
        decisionState: 'CONFIRM',
        displayName,
        rowKey: `sectors:${displayName}`,
        sectorAlignment: 'NOT_APPLICABLE',
        sectorStatus: null,
        trajectory: {
            deltaMomentum: 1,
            deltaStrength: 1,
            direction: 'UP_RIGHT',
            reason: 'Rising.',
        },
    };
}

describe('rrgGeometry', () => {
    it('keeps a single extreme observation outside the Adaptive domain without losing zero', () => {
        const rows = [
            row('A', -2, -1),
            row('B', -1, 1),
            row('C', 0.5, 0.2),
            row('D', 1.5, 2),
            row('GTWL', 171.9, 128),
        ];

        const domain = buildRrgDomain(rows, rows, 'ADAPTIVE');
        const pin = getOutlierPin(rows[4], domain);

        expect(domain.xMin).toBeLessThanOrEqual(0);
        expect(domain.yMin).toBeLessThanOrEqual(0);
        expect(domain.xMax).toBeLessThan(171.9);
        expect(domain.yMax).toBeLessThan(128);
        expect(pin).toMatchObject({
            horizontal: 'RIGHT',
            vertical: 'TOP',
            actualX: 171.9,
            actualY: 128,
        });
    });

    it('clips trail points to the correct domain boundary', () => {
        expect(
            clipPointToDomain(
                { x: 180, y: -90 },
                { xMin: -10, xMax: 10, yMin: -5, yMax: 5 },
            ),
        ).toEqual({
            x: 10,
            y: -5,
            clippedX: true,
            clippedY: true,
        });
    });
});
