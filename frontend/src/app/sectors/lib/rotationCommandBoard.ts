import type { SectorRrgRow, SectorViewMode } from './sectorTransforms';

export type RotationDecisionState =
    | 'CONFIRM'
    | 'EMERGING'
    | 'REVERSAL_WATCH'
    | 'MONITOR'
    | 'DEGRADING'
    | 'AVOID';

export type RotationTrajectoryDirection =
    | 'UP_RIGHT'
    | 'DOWN_LEFT'
    | 'MIXED'
    | 'FLAT'
    | 'UNAVAILABLE';

export type SectorAlignment =
    | 'ALIGNED'
    | 'MIXED'
    | 'UNALIGNED'
    | 'UNAVAILABLE'
    | 'NOT_APPLICABLE';

export interface RotationTrajectory {
    deltaMomentum: number | null;
    deltaStrength: number | null;
    direction: RotationTrajectoryDirection;
    reason: string;
}

export interface DerivedRotationRow extends SectorRrgRow {
    decisionState: RotationDecisionState;
    displayName: string;
    rowKey: string;
    sectorAlignment: SectorAlignment;
    sectorStatus: RotationQuadrant | null;
    trajectory: RotationTrajectory;
}

export type RotationDecisionCounts = Record<RotationDecisionState, number>;
export type RotationSortMode =
    | 'ROTATION_PRIORITY'
    | 'VELOCITY'
    | 'RELATIVE_STRENGTH'
    | 'MOMENTUM'
    | 'SECTOR_ALIGNMENT'
    | 'TICKER';
export type RotationSortDirection = 'ASC' | 'DESC';

export interface RotationSortOptions {
    direction: RotationSortDirection;
    mode: RotationSortMode;
}

const VALID_QUADRANTS = ['LEADING', 'IMPROVING', 'WEAKENING', 'LAGGING'] as const;
type RotationQuadrant = typeof VALID_QUADRANTS[number] | 'UNKNOWN';

function normalizeSectorName(value: string): string {
    return value.trim().replace(/\s+/g, ' ').replace(/\s*,\s*/g, ',').toLocaleLowerCase();
}

function normalizeQuadrant(value: string): RotationQuadrant {
    const normalized = value.trim().toUpperCase();
    return VALID_QUADRANTS.includes(normalized as Exclude<RotationQuadrant, 'UNKNOWN'>)
        ? normalized as Exclude<RotationQuadrant, 'UNKNOWN'>
        : 'UNKNOWN';
}

interface DeriveRotationRowOptions {
    sectorRows: SectorRrgRow[];
    viewMode: SectorViewMode;
}

function deriveTrajectory(row: SectorRrgRow): RotationTrajectory {
    if (!Number.isFinite(row.x) || !Number.isFinite(row.y)) {
        return {
            deltaMomentum: null,
            deltaStrength: null,
            direction: 'UNAVAILABLE',
            reason: 'Current momentum or relative strength is unavailable.',
        };
    }

    const trail = (Array.isArray(row.trail) ? row.trail : []).filter(
        (point) => Number.isFinite(point.x) && Number.isFinite(point.y),
    );
    if (trail.length < 2) {
        return {
            deltaMomentum: null,
            deltaStrength: null,
            direction: 'UNAVAILABLE',
            reason: 'At least two valid trail points are required.',
        };
    }

    const latestTrailPoint = trail[trail.length - 1];
    if (
        Math.abs(latestTrailPoint.x - row.x) > 0.005
        || Math.abs(latestTrailPoint.y - row.y) > 0.005
    ) {
        return {
            deltaMomentum: null,
            deltaStrength: null,
            direction: 'UNAVAILABLE',
            reason: 'The current endpoint does not match the latest trail point.',
        };
    }

    const reference = trail[Math.max(0, trail.length - 5)];
    const deltaMomentum = row.x - reference.x;
    const deltaStrength = row.y - reference.y;
    const direction: RotationTrajectoryDirection =
        deltaMomentum > 0 && deltaStrength > 0
            ? 'UP_RIGHT'
            : deltaMomentum < 0 && deltaStrength < 0
                ? 'DOWN_LEFT'
                : deltaMomentum === 0 && deltaStrength === 0
                    ? 'FLAT'
                    : 'MIXED';

    return {
        deltaMomentum,
        deltaStrength,
        direction,
        reason: direction === 'UP_RIGHT'
            ? 'Momentum and relative strength are rising.'
            : direction === 'DOWN_LEFT'
                ? 'Momentum and relative strength are falling.'
                : direction === 'FLAT'
                    ? 'Rotation is flat.'
                    : 'Rotation is mixed.',
    };
}

export function deriveRotationRow(
    row: SectorRrgRow,
    options: DeriveRotationRowOptions,
): DerivedRotationRow {
    const trajectory = deriveTrajectory(row);
    const direction = trajectory.direction;
    const displayName = row.ticker || row.Sector;
    const quadrant = normalizeQuadrant(row.Status);
    const matchingSectorRows = options.sectorRows.filter(
        (sectorRow) => normalizeSectorName(sectorRow.Sector) === normalizeSectorName(row.Sector),
    );
    const sectorStatus = matchingSectorRows.length === 1
        ? normalizeQuadrant(matchingSectorRows[0].Status)
        : null;
    const sectorAlignment: SectorAlignment = options.viewMode === 'sectors'
        ? 'NOT_APPLICABLE'
        : sectorStatus === 'LEADING' || sectorStatus === 'IMPROVING'
            ? 'ALIGNED'
            : sectorStatus === 'WEAKENING'
                ? 'MIXED'
                : sectorStatus === 'LAGGING'
                    ? 'UNALIGNED'
                    : 'UNAVAILABLE';
    const sectorConfirms = sectorAlignment === 'ALIGNED';
    let decisionState: RotationDecisionState = 'MONITOR';
    if (quadrant === 'WEAKENING') {
        decisionState = 'DEGRADING';
    } else if (quadrant === 'LEADING' && direction === 'DOWN_LEFT') {
        decisionState = 'DEGRADING';
    } else if (quadrant === 'LEADING' && direction === 'UP_RIGHT') {
        decisionState = 'CONFIRM';
    } else if (quadrant === 'IMPROVING' && direction === 'UP_RIGHT') {
        decisionState = 'EMERGING';
    } else if (quadrant === 'LAGGING' && direction === 'DOWN_LEFT') {
        decisionState = 'AVOID';
    } else if (
        options.viewMode === 'stocks'
        && quadrant === 'LAGGING'
        && direction === 'UP_RIGHT'
        && sectorConfirms
    ) {
        decisionState = 'REVERSAL_WATCH';
    }

    return {
        ...row,
        decisionState,
        displayName,
        rowKey: `${options.viewMode}:${displayName}`,
        sectorAlignment,
        sectorStatus,
        trajectory,
    };
}

export function filterRotationRows(
    rows: DerivedRotationRow[],
    activeStates: ReadonlySet<RotationDecisionState>,
): DerivedRotationRow[] {
    if (activeStates.size === 0) return rows;
    return rows.filter((row) => activeStates.has(row.decisionState));
}

export function countRotationDecisions(rows: DerivedRotationRow[]): RotationDecisionCounts {
    return rows.reduce<RotationDecisionCounts>(
        (counts, row) => {
            counts[row.decisionState] += 1;
            return counts;
        },
        {
            CONFIRM: 0,
            EMERGING: 0,
            REVERSAL_WATCH: 0,
            MONITOR: 0,
            DEGRADING: 0,
            AVOID: 0,
        },
    );
}

const DECISION_PRIORITY: Record<RotationDecisionState, number> = {
    CONFIRM: 6,
    EMERGING: 5,
    REVERSAL_WATCH: 4,
    MONITOR: 3,
    DEGRADING: 2,
    AVOID: 1,
};

const ALIGNMENT_PRIORITY: Record<SectorAlignment, number | null> = {
    ALIGNED: 3,
    MIXED: 2,
    UNALIGNED: 1,
    UNAVAILABLE: null,
    NOT_APPLICABLE: null,
};

function compareDisplayName(a: DerivedRotationRow, b: DerivedRotationRow): number {
    return a.displayName.localeCompare(b.displayName, undefined, { sensitivity: 'base' });
}

function compareNullableNumber(
    a: number | null | undefined,
    b: number | null | undefined,
    direction: RotationSortDirection,
): number {
    const aValid = typeof a === 'number' && Number.isFinite(a);
    const bValid = typeof b === 'number' && Number.isFinite(b);
    if (!aValid && !bValid) return 0;
    if (!aValid) return 1;
    if (!bValid) return -1;
    return direction === 'DESC' ? b - a : a - b;
}

export function sortRotationRows(
    rows: DerivedRotationRow[],
    options: RotationSortOptions,
): DerivedRotationRow[] {
    return [...rows].sort((a, b) => {
        if (options.mode === 'TICKER') {
            const nameComparison = compareDisplayName(a, b);
            return options.direction === 'DESC' ? -nameComparison : nameComparison;
        }

        if (options.mode === 'ROTATION_PRIORITY') {
            const stateComparison = options.direction === 'DESC'
                ? DECISION_PRIORITY[b.decisionState] - DECISION_PRIORITY[a.decisionState]
                : DECISION_PRIORITY[a.decisionState] - DECISION_PRIORITY[b.decisionState];
            if (stateComparison !== 0) return stateComparison;
            const velocityComparison = compareNullableNumber(a.Velocity, b.Velocity, options.direction);
            return velocityComparison || compareDisplayName(a, b);
        }

        const valueComparison = options.mode === 'VELOCITY'
            ? compareNullableNumber(a.Velocity, b.Velocity, options.direction)
            : options.mode === 'RELATIVE_STRENGTH'
                ? compareNullableNumber(a.y, b.y, options.direction)
                : options.mode === 'MOMENTUM'
                    ? compareNullableNumber(a.x, b.x, options.direction)
                    : compareNullableNumber(
                        ALIGNMENT_PRIORITY[a.sectorAlignment],
                        ALIGNMENT_PRIORITY[b.sectorAlignment],
                        options.direction,
                    );
        return valueComparison || compareDisplayName(a, b);
    });
}
