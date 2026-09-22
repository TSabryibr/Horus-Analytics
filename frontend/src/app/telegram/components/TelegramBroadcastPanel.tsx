'use client';

import { Image as ImageIcon, Type } from 'lucide-react';
import Image from 'next/image';

type TelegramBroadcastPanelProps = {
    message: string;
    image: string | null;
    sending: boolean;
    setMessage: (value: string) => void;
    setImage: (value: string | null) => void;
    onBroadcast: () => void | Promise<void>;
};

export function TelegramBroadcastPanel({
    message,
    image,
    sending,
    setMessage,
    setImage,
    onBroadcast,
}: TelegramBroadcastPanelProps) {
    return (
        <div className="section-surface flex h-full flex-col rounded-[1.6rem] p-5">
            <div className="mb-5 flex items-center justify-between">
                <div>
                    <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Royal Bulletin</div>
                    <h2 className="mt-2 font-heading text-xl font-black uppercase tracking-[0.12em] text-white">General Blast</h2>
                </div>
                <Type className="h-4 w-4 text-amber-200/70" />
            </div>

            <div className="flex flex-1 flex-col gap-5">
                <textarea
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                    className="control-input min-h-[150px] w-full flex-1 p-4 text-sm focus:border-primary"
                    placeholder="Type an announcement or update for all subscribers..."
                />

                {image ? (
                    <div className="relative aspect-video overflow-hidden rounded-[1.2rem] border border-white/10">
                        <Image src={image} alt="Preview" fill className="object-cover" />
                    </div>
                ) : null}

                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <label className="group inline-flex cursor-pointer items-center text-[10px] font-bold uppercase tracking-widest text-slate-500 transition-colors hover:text-primary">
                        <div className="mr-2 rounded-lg bg-white/5 p-2 group-hover:bg-primary/10">
                            <ImageIcon className="h-4 w-4" />
                        </div>
                        {image ? 'Swap Asset' : 'Attach Asset'}
                        <input
                            type="file"
                            accept="image/*"
                            className="hidden"
                            onChange={(event) => {
                                const file = event.target.files?.[0];
                                if (!file) {
                                    return;
                                }
                                const reader = new FileReader();
                                reader.onloadend = () => setImage(reader.result as string);
                                reader.readAsDataURL(file);
                            }}
                        />
                    </label>

                    <button
                        onClick={onBroadcast}
                        disabled={sending || (!message && !image)}
                        className="action-primary px-8 py-4 text-[10px] tracking-widest disabled:opacity-30 disabled:hover:scale-100"
                    >
                        {sending ? 'Processing...' : 'Blast Broadcast'}
                    </button>
                </div>
            </div>
        </div>
    );
}
