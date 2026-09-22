import { SectorRrgRow } from '../lib/sectorTransforms';

interface RRGChartProps {
    data: SectorRrgRow[];
    width?: number;
    height?: number;
}

export function RRGChart({ data, width = 800, height = 600 }: RRGChartProps) {
    if (!data || data.length === 0) return null;

    const allX = data.flatMap((row) => row.trail?.map((point) => point.x) || [row.x]);
    const allY = data.flatMap((row) => row.trail?.map((point) => point.y) || [row.y]);

    const minX = Math.min(...allX, -5);
    const maxX = Math.max(...allX, 5);
    const minY = Math.min(...allY, -5);
    const maxY = Math.max(...allY, 5);

    const padX = (maxX - minX) * 0.1;
    const padY = (maxY - minY) * 0.1;
    const xMin = minX - padX;
    const xMax = maxX + padX;
    const yMin = minY - padY;
    const yMax = maxY + padY;

    const margin = { top: 40, right: 40, bottom: 50, left: 60 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const xScale = (x: number) => margin.left + ((x - xMin) / (xMax - xMin)) * chartWidth;
    const yScale = (y: number) => margin.top + chartHeight - ((y - yMin) / (yMax - yMin)) * chartHeight;

    const zeroX = xScale(0);
    const zeroY = yScale(0);

    const getColor = (status: string) => {
        if (status === 'LEADING') return '#22c55e';
        if (status === 'WEAKENING') return '#eab308';
        if (status === 'IMPROVING') return '#3b82f6';
        return '#ef4444';
    };

    return (
        <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
            <rect x={margin.left} y={margin.top} width={zeroX - margin.left} height={zeroY - margin.top} fill="#3b82f6" fillOpacity="0.15" />
            <rect x={zeroX} y={margin.top} width={margin.left + chartWidth - zeroX} height={zeroY - margin.top} fill="#22c55e" fillOpacity="0.15" />
            <rect x={margin.left} y={zeroY} width={zeroX - margin.left} height={margin.top + chartHeight - zeroY} fill="#ef4444" fillOpacity="0.15" />
            <rect x={zeroX} y={zeroY} width={margin.left + chartWidth - zeroX} height={margin.top + chartHeight - zeroY} fill="#eab308" fillOpacity="0.15" />

            <text x={margin.left + 10} y={margin.top + 20} fill="#3b82f6" fontSize="12" fontWeight="bold" opacity="0.7">IMPROVING</text>
            <text x={margin.left + chartWidth - 70} y={margin.top + 20} fill="#22c55e" fontSize="12" fontWeight="bold" opacity="0.7">LEADING</text>
            <text x={margin.left + 10} y={margin.top + chartHeight - 10} fill="#ef4444" fontSize="12" fontWeight="bold" opacity="0.7">LAGGING</text>
            <text x={margin.left + chartWidth - 80} y={margin.top + chartHeight - 10} fill="#eab308" fontSize="12" fontWeight="bold" opacity="0.7">WEAKENING</text>

            {Array.from({ length: 11 }, (_, i) => {
                const val = xMin + (i / 10) * (xMax - xMin);
                const x = xScale(val);
                return <line key={`gx-${i}`} x1={x} y1={margin.top} x2={x} y2={margin.top + chartHeight} stroke="#ffffff" strokeOpacity="0.05" />;
            })}
            {Array.from({ length: 11 }, (_, i) => {
                const val = yMin + (i / 10) * (yMax - yMin);
                const y = yScale(val);
                return <line key={`gy-${i}`} x1={margin.left} y1={y} x2={margin.left + chartWidth} y2={y} stroke="#ffffff" strokeOpacity="0.05" />;
            })}

            <line x1={zeroX} y1={margin.top} x2={zeroX} y2={margin.top + chartHeight} stroke="#ffffff" strokeWidth="2" strokeOpacity="0.3" />
            <line x1={margin.left} y1={zeroY} x2={margin.left + chartWidth} y2={zeroY} stroke="#ffffff" strokeWidth="2" strokeOpacity="0.3" />

            <text x={width / 2} y={height - 10} fill="#64748b" fontSize="11" textAnchor="middle" fontWeight="bold">JdK RS-Ratio (Momentum)</text>
            <text x={15} y={height / 2} fill="#64748b" fontSize="11" textAnchor="middle" fontWeight="bold" transform={`rotate(-90, 15, ${height / 2})`}>JdK RS-Momentum (Strength)</text>

            {Array.from({ length: 5 }, (_, i) => {
                const val = xMin + (i / 4) * (xMax - xMin);
                const x = xScale(val);
                return (
                    <text key={`tx-${i}`} x={x} y={margin.top + chartHeight + 15} fill="#64748b" fontSize="9" textAnchor="middle">
                        {val.toFixed(1)}
                    </text>
                );
            })}
            {Array.from({ length: 5 }, (_, i) => {
                const val = yMin + (i / 4) * (yMax - yMin);
                const y = yScale(val);
                return (
                    <text key={`ty-${i}`} x={margin.left - 10} y={y + 3} fill="#64748b" fontSize="9" textAnchor="end">
                        {val.toFixed(1)}
                    </text>
                );
            })}

            {data.map((item, idx) => {
                const trail = item.trail || [{ x: item.x, y: item.y }];
                const color = getColor(item.Status);
                const name = item.ticker || item.Sector;

                const pathD = trail.map((point, i) => {
                    const x = xScale(point.x);
                    const y = yScale(point.y);
                    return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
                }).join(' ');

                const lastPt = trail[trail.length - 1];
                const lastX = xScale(lastPt.x);
                const lastY = yScale(lastPt.y);

                return (
                    <g key={idx}>
                        <path d={pathD} fill="none" stroke={color} strokeWidth="1.5" strokeOpacity="0.6" />
                        {trail.slice(0, -1).map((point, i) => (
                            <circle key={i} cx={xScale(point.x)} cy={yScale(point.y)} r="2" fill={color} fillOpacity="0.4" />
                        ))}
                        <circle cx={lastX} cy={lastY} r="5" fill={color} stroke="#fff" strokeWidth="1" />
                        {trail.length > 1 && (
                            <polygon
                                points={`${lastX},${lastY - 8} ${lastX - 4},${lastY - 4} ${lastX + 4},${lastY - 4}`}
                                fill={color}
                                transform={`rotate(${Math.atan2(
                                    yScale(trail[trail.length - 2].y) - lastY,
                                    xScale(trail[trail.length - 2].x) - lastX
                                ) * 180 / Math.PI + 90}, ${lastX}, ${lastY})`}
                            />
                        )}
                        <text
                            x={lastX}
                            y={lastY - 10}
                            fill={color}
                            fontSize="10"
                            fontWeight="bold"
                            textAnchor="middle"
                            className="pointer-events-none"
                            style={{ textShadow: '0 0 3px rgba(0,0,0,0.8), 0 0 6px rgba(0,0,0,0.5)' }}
                        >
                            {name}
                        </text>
                    </g>
                );
            })}
        </svg>
    );
}
