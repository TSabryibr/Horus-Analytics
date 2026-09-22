import { Shield } from 'lucide-react';

export function TrapsEmptyBanner() {
    return (
        <div className="bg-emerald-900/10 border border-emerald-500/20 rounded-xl p-6 text-center">
            <Shield className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-emerald-400">The Market is Honest Today</h3>
            <p className="text-gray-400">No major traps detected in the last window.</p>
        </div>
    );
}
