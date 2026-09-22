import { ReactNode } from 'react';
import { Layers, X } from 'lucide-react';

interface SectorFullscreenModalProps {
    children: ReactNode;
    isOpen: boolean;
    onClose: () => void;
}

export function SectorFullscreenModal({
    children,
    isOpen,
    onClose,
}: SectorFullscreenModalProps) {
    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 bg-[#030712] flex flex-col"
            data-testid="sector-fullscreen-backdrop"
            onClick={(event) => {
                if (event.target === event.currentTarget) {
                    onClose();
                }
            }}
        >
            <div className="flex items-center justify-between p-4 border-b border-white/5">
                <div className="flex items-center gap-3">
                    <Layers className="w-6 h-6 text-purple-400" />
                    <span className="text-lg font-black text-white uppercase tracking-tight">Alfheim RRG - Fullscreen</span>
                    <span className="text-xs text-slate-500">Press ESC to close</span>
                </div>
                <button
                    aria-label="Close fullscreen RRG"
                    onClick={onClose}
                    className="p-2 bg-slate-800 hover:bg-slate-700 rounded-xl transition"
                >
                    <X className="w-5 h-5 text-white" />
                </button>
            </div>
            <div className="flex-1 p-4">{children}</div>
        </div>
    );
}
