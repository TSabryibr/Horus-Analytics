import { memo } from 'react';
import { TrendingUp, TrendingDown, Send } from 'lucide-react';
import clsx from 'clsx';
import { AnalyticsItem } from '@/types';
import { PromoteToDeskButtons, SignalDeskLaneKey } from '../../components/signal-desk/PromoteToDeskButtons';

interface AnalyticsRowProps {
    item: AnalyticsItem;
    onBroadcast?: (item: AnalyticsItem) => void;
    onPromoteCandidate?: (item: AnalyticsItem, lane: SignalDeskLaneKey) => void | Promise<unknown>;
    columns: {
        Ticker: boolean;
        Price: boolean;
        Score: boolean;
        Status: boolean;
        Trend: boolean;
        RSI: boolean;
        Target_1: boolean;
        Target_2: boolean;
        Risk_Reward: boolean;
        Stop_Loss: boolean;
        Volume: boolean;
        ATR: boolean;
    };
}

export const AnalyticsRow = memo(({ item, columns, onBroadcast, onPromoteCandidate }: AnalyticsRowProps) => {
    return (
        <tr className="transition hover:bg-white/[0.03]">
            {columns.Ticker && (
                <td className="px-6 py-4 font-medium">
                    <div className="flex items-center gap-1.5">
                        <span>{item.Ticker}</span>
                        {Number(item.Signal_Score || 0) >= 8.0 && (
                            <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 tracking-wider">
                                HIGH CONVICTION ⚡
                            </span>
                        )}
                        {item.Institutional_Signal === "✅" && <span className="ml-1 text-xs bg-purple-500/20 text-purple-400 px-1.5 py-0.5 rounded">INST</span>}
                    </div>
                </td>
            )}
            {columns.Price && (
                <td className="px-6 py-4 text-white font-mono">
                    {item.Price?.toFixed(4)}
                </td>
            )}
            {columns.Score && (
                <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                        <span className={clsx("px-2 py-1 rounded font-bold text-xs",
                            item.Signal_Score >= 8 ? "bg-green-500/20 text-green-400" :
                                item.Signal_Score >= 5 ? "bg-yellow-500/20 text-yellow-400" :
                                    "bg-red-500/20 text-red-400"
                        )}>
                            {item.Signal_Score}/10
                        </span>
                        {item.Signal_Score > 5 && (
                            <button
                                type="button"
                                onClick={() => onBroadcast?.(item)}
                                aria-label={`Broadcast ${item.Ticker} to Telegram`}
                                className="p-1.5 rounded-full hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 transition-all hover:scale-110"
                                title="Broadcast to Telegram"
                            >
                                <Send className="h-3 w-3" />
                            </button>
                        )}
                    </div>
                </td>
            )}
            {columns.Status && (
                <td className="px-6 py-4 font-medium text-gray-300">
                    {item.Status}
                </td>
            )}
            {columns.Trend && (
                <td className="px-6 py-4">
                    {item.Trend === 'BULLISH' ?
                        <span className="flex items-center text-green-400"><TrendingUp className="h-4 w-4 mr-1" /> Bullish</span> :
                        <span className="flex items-center text-red-400"><TrendingDown className="h-4 w-4 mr-1" /> Bearish</span>
                    }
                </td>
            )}
            {columns.RSI && (
                <td className={clsx("px-6 py-4 font-mono",
                    item.RSI > 70 ? "text-red-400" : item.RSI < 30 ? "text-green-400" : "text-gray-400"
                )}>
                    {item.RSI}
                </td>
            )}
            {columns.Target_1 && <td className="px-6 py-4 text-green-400">{item.Target_1}</td>}
            {columns.Target_2 && (
                <td className="px-6 py-4 text-green-400 font-mono">
                    {(() => {
                        const n = Number(item.Target_2);
                        const factor = Math.pow(10, 3);
                        return (Math.trunc(n * factor) / factor).toFixed(3);
                    })()}
                </td>
            )}
            {columns.Risk_Reward && (
                <td className="px-6 py-4">
                    {item.Risk_Reward_Ratio}x
                </td>
            )}
            {columns.Stop_Loss && <td className="px-6 py-4 text-red-400">{item.Stop_Loss}</td>}
            {/* Extra Data */}
            {columns.Volume && <td className="px-6 py-4">{item.Avg_Turnover_M}</td>}
            {columns.ATR && <td className="px-6 py-4">{item.ATR}</td>}
            <td className="px-6 py-4">
                {onPromoteCandidate && item.Price ? (
                    <PromoteToDeskButtons compact onPromote={(lane) => onPromoteCandidate(item, lane)} />
                ) : null}
            </td>
        </tr>
    );
});

AnalyticsRow.displayName = 'AnalyticsRow';
