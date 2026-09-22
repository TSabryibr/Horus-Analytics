import { useState } from 'react';

type WeeklyReportNotesPanelProps = {
    notes: string[];
    warnings: string[];
};

const MAX_VISIBLE = 8;

export function WeeklyReportNotesPanel({
    notes,
    warnings,
}: WeeklyReportNotesPanelProps) {
    const [showAllWarnings, setShowAllWarnings] = useState(false);
    const [showAllNotes, setShowAllNotes] = useState(false);

    if (warnings.length === 0 && notes.length === 0) {
        return null;
    }

    const visibleWarnings = showAllWarnings ? warnings : warnings.slice(0, MAX_VISIBLE);
    const hiddenWarnings = warnings.length - MAX_VISIBLE;
    const visibleNotes = showAllNotes ? notes : notes.slice(0, MAX_VISIBLE);
    const hiddenNotes = notes.length - MAX_VISIBLE;

    return (
        <div className="section-surface p-6 rounded-2xl">
            <h3 className="text-sm font-bold uppercase tracking-widest text-amber-300 mb-4">Report Notes</h3>
            <div className="space-y-2">
                {visibleWarnings.map((line, idx) => (
                    <p key={`w-${idx}`} className="text-xs text-amber-300">- {line}</p>
                ))}
                {!showAllWarnings && hiddenWarnings > 0 && (
                    <button
                        type="button"
                        onClick={() => setShowAllWarnings(true)}
                        className="text-[10px] text-amber-400/70 hover:text-amber-300 underline underline-offset-2 mt-1"
                    >
                        +{hiddenWarnings} more warning{hiddenWarnings > 1 ? 's' : ''} hidden
                    </button>
                )}
                {visibleNotes.map((line, idx) => (
                    <p key={`n-${idx}`} className="text-xs text-slate-300">- {line}</p>
                ))}
                {!showAllNotes && hiddenNotes > 0 && (
                    <button
                        type="button"
                        onClick={() => setShowAllNotes(true)}
                        className="text-[10px] text-slate-500 hover:text-slate-300 underline underline-offset-2 mt-1"
                    >
                        +{hiddenNotes} more note{hiddenNotes > 1 ? 's' : ''} hidden
                    </button>
                )}
            </div>
        </div>
    );
}
