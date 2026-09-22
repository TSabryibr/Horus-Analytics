import { X } from 'lucide-react';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';
import { HomeArchiveEntry } from '../lib/homeTransforms';

type HomeArchivesModalProps = {
    archivesByDate: Record<string, HomeArchiveEntry[]>;
    isOpen: boolean;
    onClose: () => void;
};

export function HomeArchivesModal({
    archivesByDate,
    isOpen,
    onClose,
}: HomeArchivesModalProps) {
    if (!isOpen) {
        return null;
    }

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 p-6" onClick={onClose}>
            <div
                className="section-surface industrial-corner relative w-full max-w-5xl border border-primary/20 p-12 transition-all"
                onClick={(event) => event.stopPropagation()}
            >
                <div className="flex items-start justify-between mb-12">
                    <div>
                        <h3 className="meta-label mb-3 text-primary">Intelligence Repository</h3>
                        <p className="text-4xl heading-title text-white tracking-tight uppercase">Matrix Archive Logs</p>
                        <div className="h-1 w-24 bg-primary/30 mt-4" />
                    </div>
                    <IndustrialButton
                        aria-label="Close archive modal"
                        onClick={onClose}
                        variant="secondary"
                        className="rounded-sm px-4 py-4 text-slate-400 hover:text-rose-300"
                    >
                        <X className="h-6 w-6" />
                    </IndustrialButton>
                </div>

                {Object.keys(archivesByDate).length === 0 ? (
                    <div className="text-center py-24 text-slate-600 meta-label tracking-[0.5em]">
                        Log Data Corrupted or Empty
                    </div>
                ) : (
                    <div className="space-y-10 max-h-[60vh] overflow-y-auto pr-6 custom-scrollbar">
                        {Object.entries(archivesByDate)
                            .sort(([left], [right]) => right.localeCompare(left))
                            .map(([date, signalEntries]) => (
                                <div key={date}>
                                    <div className="flex items-center gap-6 mb-6">
                                        <span className="text-sm font-black text-primary uppercase tracking-[0.3em] font-heading">
                                            {new Date(date).toLocaleDateString('en-US', { day: '2-digit', month: 'long', year: 'numeric' })}
                                        </span>
                                        <div className="flex-1 h-[1px] bg-white/[0.08]" />
                                        <span className="text-[10px] font-mono text-slate-500">ENTRY_COUNT: {signalEntries.length}</span>
                                    </div>
                                    <div className="grid gap-3">
                                        {signalEntries.map((signal, index) => (
                                            <div
                                                key={`${signal.ticker}-${index}`}
                                                className="flex items-center justify-between px-6 py-5 bg-white/[0.02] border border-white/5 hover:border-primary/30 hover:bg-primary/5 transition-all group"
                                            >
                                                <div className="flex items-center gap-8">
                                                    <span className="text-lg font-black text-white group-hover:text-primary transition-colors">{signal.ticker}</span>
                                                    <span className="section-surface-muted rounded-sm border border-white/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-slate-300">
                                                        {signal.signal_type}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-12">
                                                    <span className="text-sm text-slate-400 font-mono tracking-tighter">EGP{Number(signal.price).toLocaleString()}</span>
                                                    <div
                                                        className={
                                                            signal.score >= 8
                                                                ? 'text-xs font-black px-4 py-1.5 rounded-sm border bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                                                : signal.score >= 6
                                                                    ? 'text-xs font-black px-4 py-1.5 rounded-sm border bg-amber-500/10 text-amber-400 border-amber-500/20'
                                                                    : 'text-xs font-black px-4 py-1.5 rounded-sm border bg-slate-500/10 text-slate-500 border-slate-500/20'
                                                        }
                                                    >
                                                        CONF: {signal.score * 10}%
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                    </div>
                )}
            </div>
        </div>
    );
}
