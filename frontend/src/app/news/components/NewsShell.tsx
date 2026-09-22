import { Scroll, RefreshCw } from 'lucide-react';
import clsx from 'clsx';
import { ReactNode } from 'react';
import { CommandHeader } from '@/app/components/custom/CommandHeader';

interface NewsShellProps {
    loading: boolean;
    onRefresh: () => void;
    children: ReactNode;
    bifrostRegime?: string;
    articleCount?: number;
}

export function NewsShell({ loading, onRefresh, children, bifrostRegime, articleCount }: NewsShellProps) {
    return (
        <div className="page-shell">
            <CommandHeader
                eyebrow="Signal Wire"
                title="Market News Feed"
                description="Newsflow monitoring, sentiment interpretation, and market narrative tracking from the live command surface."
                icon={<Scroll className="h-7 w-7" />}
                iconClassName="border-emerald-400/20 bg-emerald-500/10 text-emerald-200 shadow-[0_16px_34px_rgba(16,185,129,0.16)]"
                statusItems={[
                    {
                        label: 'Regime',
                        value: bifrostRegime ? `${bifrostRegime.toUpperCase()} REGIME` : 'BIFROST STREAM',
                        tone: (bifrostRegime || '').toUpperCase().includes('BEAR') ? 'danger' : 'success',
                    },
                    {
                        label: 'Articles',
                        value: articleCount !== undefined ? `${articleCount} Ingested` : 'Live Wire',
                        tone: 'info',
                    },
                    { label: 'Stream', value: loading ? 'Refreshing' : 'Live Feed', tone: loading ? 'warning' : 'success' },
                    { label: 'Mode', value: 'Bifrost AI', tone: 'muted' },
                ]}
                actions={
                    <button
                        onClick={onRefresh}
                        disabled={loading}
                        aria-label="Refresh news feed"
                        className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-2.5 transition hover:border-emerald-400/25 hover:bg-white/[0.05] disabled:opacity-50"
                    >
                        <RefreshCw className={clsx('h-5 w-5 text-slate-300', loading && 'animate-spin')} />
                    </button>
                }
            />
            {children}
        </div>
    );
}
