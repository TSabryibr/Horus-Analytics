'use client';

interface StatusSchedulerPanelProps {
    jobs: Array<{ id: string; trigger: string; next_run?: string | null }>;
}

export function StatusSchedulerPanel({ jobs }: StatusSchedulerPanelProps) {
    return (
        <div className="bg-[#0A0D14] border border-white/10 rounded-3xl p-8">
            <div className="flex items-center gap-3 mb-8">
                <h2 className="text-xl font-bold text-white uppercase tracking-tighter">Job Scheduler Pipeline</h2>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b border-white/5 text-[10px] text-slate-400 uppercase font-black uppercase tracking-widest">
                            <th className="pb-4 pr-4">Task ID</th>
                            <th className="pb-4 pr-4 text-right">Trigger Mechanism</th>
                            <th className="pb-4 text-right">Target Execution Time</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {jobs.length ? (
                            jobs.map((job) => (
                                <tr key={job.id} className="group">
                                    <td className="py-4 pr-4 font-bold text-slate-300 group-hover:text-primary transition-colors uppercase tracking-tight text-xs">
                                        {job.id}
                                    </td>
                                    <td className="py-4 pr-4 text-right">
                                        <code className="bg-slate-900 text-[10px] px-2 py-1 rounded text-slate-500 font-mono">
                                            {job.trigger}
                                        </code>
                                    </td>
                                    <td className="py-4 text-right font-mono text-[11px] text-slate-400">
                                        {job.next_run || 'Asynchronous'}
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={3} className="py-5 text-center text-xs font-bold text-slate-500">
                                    Job list refreshing
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
