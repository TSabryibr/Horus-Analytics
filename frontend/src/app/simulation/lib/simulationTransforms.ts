export function formatSimulationChartData(paths: number[][]): Array<Record<string, number>> {
    if (!paths || paths.length === 0) {
        return [];
    }

    const numDays = paths[0].length;
    const data: Array<Record<string, number>> = [];

    for (let i = 0; i < numDays; i += 1) {
        const entry: Record<string, number> = { name: i };
        paths.forEach((path, idx) => {
            entry[`p${idx}`] = path[i];
        });
        data.push(entry);
    }

    return data;
}
