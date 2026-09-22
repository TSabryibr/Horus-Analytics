'use client';

import { WeeklyReportNotesPanel } from './components/WeeklyReportNotesPanel';
import { WeeklyReportOverview } from './components/WeeklyReportOverview';
import { WeeklyReportShell } from './components/WeeklyReportShell';
import { WeeklyReportSummaryPanel } from './components/WeeklyReportSummaryPanel';
import { useWeeklyReportActions } from './hooks/useWeeklyReportActions';
import { useWeeklyReportRuntime } from './hooks/useWeeklyReportRuntime';

export default function WeeklyReportPage() {
    const {
        period,
        setPeriod,
        data,
        loading,
        error,
        feedback,
        setFeedback,
        loadReport,
        market,
        review,
        keyShifts,
        worked,
        failed,
        warnings,
        notes,
        recommendations,
        cacheInfo,
    } = useWeeklyReportRuntime();

    const { broadcasting, broadcastReport } = useWeeklyReportActions({
        period,
        loadReport,
        setFeedback,
    });

    return (
        <WeeklyReportShell
            broadcasting={broadcasting}
            cacheInfo={cacheInfo}
            error={error}
            feedback={feedback}
            loading={loading}
            onBroadcast={broadcastReport}
            onRefresh={() => void loadReport(true)}
            onSetPeriod={setPeriod}
            period={period}
        >
            <WeeklyReportOverview
                data={data}
                market={market}
                review={review}
            />
            <WeeklyReportSummaryPanel
                failed={failed}
                keyShifts={keyShifts}
                market={market}
                recommendations={recommendations}
                review={review}
                worked={worked}
            />
            <WeeklyReportNotesPanel
                notes={notes}
                warnings={warnings}
            />
        </WeeklyReportShell>
    );
}
