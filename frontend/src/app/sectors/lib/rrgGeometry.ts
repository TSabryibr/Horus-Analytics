import type { DerivedRotationRow } from './rotationCommandBoard';

export type RrgScaleMode = 'ADAPTIVE' | 'FULL_RANGE' | 'FOCUS_FILTER';

export interface RrgDomain {
    xMax: number;
    xMin: number;
    yMax: number;
    yMin: number;
}

export interface RrgOutlierPin {
    actualX: number;
    actualY: number;
    horizontal: 'LEFT' | 'RIGHT' | null;
    vertical: 'BOTTOM' | 'TOP' | null;
}

export interface ClippedRrgPoint {
    clippedX: boolean;
    clippedY: boolean;
    x: number;
    y: number;
}

function percentile(values: number[], p: number): number {
    if (values.length === 1) return values[0];
    const position = (values.length - 1) * p;
    const lower = Math.floor(position);
    const upper = Math.ceil(position);
    const weight = position - lower;
    return values[lower] * (1 - weight) + values[upper] * weight;
}

function robustBounds(values: number[]): [number, number] {
    const sorted = [...values].sort((a, b) => a - b);
    if (sorted.length < 4) return [sorted[0], sorted[sorted.length - 1]];
    const q1 = percentile(sorted, 0.25);
    const q3 = percentile(sorted, 0.75);
    const iqr = q3 - q1;
    if (iqr === 0) return [q1, q3];
    const lowerFence = q1 - 1.5 * iqr;
    const upperFence = q3 + 1.5 * iqr;
    const inliers = sorted.filter((value) => value >= lowerFence && value <= upperFence);
    return [inliers[0] ?? q1, inliers[inliers.length - 1] ?? q3];
}

function paddedAxisBounds(minValue: number, maxValue: number): [number, number] {
    let min = Math.min(minValue, 0);
    let max = Math.max(maxValue, 0);
    if (min === max) {
        min -= 0.5;
        max += 0.5;
    }
    const span = Math.max(max - min, 1);
    const padding = span * 0.1;
    min -= padding;
    max += padding;
    return [min, max];
}

function validEndpoints(rows: DerivedRotationRow[]): Array<{ x: number; y: number }> {
    return rows
        .filter((row) => Number.isFinite(row.x) && Number.isFinite(row.y))
        .map((row) => ({ x: row.x, y: row.y }));
}

export function buildRrgDomain(
    allRows: DerivedRotationRow[],
    visibleRows: DerivedRotationRow[],
    mode: RrgScaleMode,
): RrgDomain {
    const population = mode === 'FOCUS_FILTER' ? visibleRows : allRows;
    const points = mode === 'FULL_RANGE'
        ? population.flatMap((row) => [
            ...(row.trail ?? []).filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y)),
            ...(Number.isFinite(row.x) && Number.isFinite(row.y) ? [{ x: row.x, y: row.y }] : []),
        ])
        : validEndpoints(population);

    if (points.length === 0) {
        return { xMin: -1, xMax: 1, yMin: -1, yMax: 1 };
    }

    const xValues = points.map((point) => point.x);
    const yValues = points.map((point) => point.y);
    const [rawXMin, rawXMax] = mode === 'FULL_RANGE'
        ? [Math.min(...xValues), Math.max(...xValues)]
        : robustBounds(xValues);
    const [rawYMin, rawYMax] = mode === 'FULL_RANGE'
        ? [Math.min(...yValues), Math.max(...yValues)]
        : robustBounds(yValues);
    const [xMin, xMax] = paddedAxisBounds(rawXMin, rawXMax);
    const [yMin, yMax] = paddedAxisBounds(rawYMin, rawYMax);

    return { xMin, xMax, yMin, yMax };
}

export function getOutlierPin(
    row: DerivedRotationRow,
    domain: RrgDomain,
): RrgOutlierPin | null {
    if (!Number.isFinite(row.x) || !Number.isFinite(row.y)) return null;
    const horizontal = row.x < domain.xMin ? 'LEFT' : row.x > domain.xMax ? 'RIGHT' : null;
    const vertical = row.y < domain.yMin ? 'BOTTOM' : row.y > domain.yMax ? 'TOP' : null;
    if (!horizontal && !vertical) return null;
    return {
        actualX: row.x,
        actualY: row.y,
        horizontal,
        vertical,
    };
}

export function clipPointToDomain(
    point: { x: number; y: number },
    domain: RrgDomain,
): ClippedRrgPoint {
    return {
        x: Math.min(domain.xMax, Math.max(domain.xMin, point.x)),
        y: Math.min(domain.yMax, Math.max(domain.yMin, point.y)),
        clippedX: point.x < domain.xMin || point.x > domain.xMax,
        clippedY: point.y < domain.yMin || point.y > domain.yMax,
    };
}
