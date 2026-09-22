'use client';

import { useEffect, memo } from 'react';
import { AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

type ConfirmTone = 'default' | 'danger' | 'warning';

interface ConfirmDialogProps {
    isOpen: boolean;
    title: string;
    description?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    confirming?: boolean;
    tone?: ConfirmTone;
    onConfirm: () => void | Promise<void>;
    onClose: () => void;
}

const ConfirmDialog = memo(function ConfirmDialog({
    isOpen,
    title,
    description,
    confirmLabel = 'Confirm',
    cancelLabel = 'Cancel',
    confirming = false,
    tone = 'default',
    onConfirm,
    onClose
}: ConfirmDialogProps) {
    useEffect(() => {
        if (!isOpen) return;

        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape' && !confirming) {
                onClose();
            }
        };

        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [confirming, isOpen, onClose]);

    if (!isOpen) return null;

    const confirmButtonClass =
        tone === 'danger'
            ? 'action-primary !bg-rose-600 hover:!bg-rose-500 !text-white'
            : tone === 'warning'
                ? 'action-primary !bg-amber-500 hover:!bg-amber-400 !text-black'
                : 'action-primary';

    return (
        <div
            className="fixed inset-0 z-[130] flex items-center justify-center bg-black/60 p-4"
            onClick={(event) => {
                if (event.target === event.currentTarget && !confirming) {
                    onClose();
                }
            }}
            role="dialog"
            aria-modal="true"
            aria-label={title}
        >
            <div className="section-surface w-full max-w-md p-6">
                <div className="mb-5 flex items-start gap-3">
                    <div className="rounded-lg bg-amber-500/15 p-2 text-amber-300">
                        <AlertTriangle className="h-4 w-4" />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-white">{title}</h2>
                        {description && (
                            <p className="mt-1 text-sm text-slate-300">{description}</p>
                        )}
                    </div>
                </div>

                <div className="flex items-center justify-end gap-3">
                    <button
                        type="button"
                        className="action-secondary"
                        onClick={onClose}
                        disabled={confirming}
                    >
                        {cancelLabel}
                    </button>
                    <button
                        type="button"
                        className={clsx(confirmButtonClass, confirming && 'opacity-70')}
                        onClick={() => {
                            void onConfirm();
                        }}
                        disabled={confirming}
                    >
                        {confirming ? 'Working...' : confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
});

export default ConfirmDialog;
