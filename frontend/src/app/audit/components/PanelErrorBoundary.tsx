'use client';

import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
    children: ReactNode;
    panelName: string;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class PanelErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error(`[${this.props.panelName}] Panel error:`, error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="col-span-12 section-surface rounded-3xl p-6">
                    <div className="flex flex-col items-center justify-center space-y-3 py-8 text-center">
                        <AlertTriangle className="h-8 w-8 text-amber-400" />
                        <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
                            {this.props.panelName} failed to render
                        </p>
                        <p className="max-w-md text-[11px] text-slate-500">
                            {this.state.error?.message || 'An unexpected error occurred.'}
                        </p>
                        <button
                            type="button"
                            onClick={() => this.setState({ hasError: false, error: null })}
                            className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em] text-slate-300 transition hover:bg-white/[0.06]"
                        >
                            <RefreshCw size={10} /> Retry
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
