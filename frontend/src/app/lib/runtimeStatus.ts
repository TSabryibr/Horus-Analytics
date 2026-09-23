export type RuntimeSurfaceState = {
  code: 'SYNCING' | 'PROVISIONING' | 'PROVISIONING_ERROR' | 'DETECTING' | 'STALE' | 'FRESH';
  label: string;
  textClass: string;
  dotClass: string;
};

type RuntimeStateInput = {
  isSyncing: boolean;
  backendKnown: boolean;
  provisioningStatus?: string | null;
  pipelineState?: string | null;
  marketOpen?: boolean | null;
  historyStatus?: string | null;
  intradayStatus?: string | null;
  historyOk?: boolean | null;
  intradayOk?: boolean | null;
};

export function resolveRuntimeSurfaceState({
  isSyncing,
  backendKnown,
  provisioningStatus,
  pipelineState,
  marketOpen,
  historyStatus,
  intradayStatus,
  historyOk,
  intradayOk,
}: RuntimeStateInput): RuntimeSurfaceState {
  if (isSyncing) {
    return {
      code: 'SYNCING',
      label: 'Syncing Data...',
      textClass: 'text-cyan-400',
      dotClass: 'bg-cyan-500',
    };
  }

  if (String(provisioningStatus || '').toUpperCase() === 'RUNNING') {
    return {
      code: 'PROVISIONING',
      label: 'Provisioning History',
      textClass: 'text-cyan-400',
      dotClass: 'bg-cyan-500',
    };
  }

  if (String(provisioningStatus || '').toUpperCase() === 'ERROR') {
    return {
      code: 'PROVISIONING_ERROR',
      label: 'Provisioning Failed',
      textClass: 'text-rose-500',
      dotClass: 'bg-rose-500',
    };
  }

  if (!backendKnown) {
    return {
      code: 'DETECTING',
      label: 'Detecting Feed',
      textClass: 'text-cyan-400',
      dotClass: 'bg-cyan-500',
    };
  }

  const normalizedHistory = String(historyStatus || '').toUpperCase();
  const normalizedIntraday = String(intradayStatus || '').toUpperCase();
  const normalizedPipeline = String(pipelineState || '').toUpperCase();
  const marketIsOpen = marketOpen !== false;
  const historyFresh = normalizedHistory === 'FRESH' || historyOk === true;
  const intradayFresh = normalizedIntraday === 'LIVE' || normalizedIntraday === 'FRESH' || intradayOk === true;

  if (normalizedPipeline === 'FRESH' || (historyFresh && (!marketIsOpen || intradayFresh))) {
    return {
      code: 'FRESH',
      label: 'All Systems Go',
      textClass: 'text-emerald-400',
      dotClass: 'bg-emerald-500',
    };
  }

  return {
    code: 'STALE',
    label: 'Data Latency',
    textClass: 'text-amber-500',
    dotClass: 'bg-amber-500',
  };
}
