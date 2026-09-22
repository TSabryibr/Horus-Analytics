export function deriveSupportedRuntimeFeatures(preflightResult: any): string[] {
    const supportedNodes = new Set(
        Array.isArray(preflightResult?.supported_nodes)
            ? preflightResult.supported_nodes.map((node: string) => String(node).toLowerCase())
            : []
    );
    const definitions = Object.values(preflightResult?.plan?.definitions ?? {}) as Array<Record<string, any>>;
    const hasMacdTuple = definitions.some((definition) =>
        definition?.node_type === 'TUPLE_ITEM' && String(definition?.source?.name ?? '').toLowerCase() === 'ta.macd'
    );

    const features: string[] = [];

    if (supportedNodes.has('ta.rsi')) {
        features.push('RSI threshold and boolean conditions');
    }
    if (supportedNodes.has('request.security')) {
        features.push('Same-symbol higher-timeframe security imports');
    }
    if (supportedNodes.has('ta.atr')) {
        features.push('ATR threshold conditions');
    }
    if (supportedNodes.has('ta.highest') || supportedNodes.has('ta.lowest')) {
        features.push('Highest/lowest breakout conditions');
    }
    if (supportedNodes.has('ta.wma') || supportedNodes.has('ta.vwma')) {
        features.push('WMA/VWMA trend conditions');
    }
    if (supportedNodes.has('ta.linreg')) {
        features.push('Linear regression trend conditions');
    }
    if (supportedNodes.has('ta.alma')) {
        features.push('ALMA smoothing conditions');
    }
    if (supportedNodes.has('ta.macd') || hasMacdTuple) {
        features.push('MACD tuple crossover/crossunder');
    }
    if (supportedNodes.has('ta.sma')) {
        features.push('SMA signal conditions');
    }
    if (supportedNodes.has('ta.ema')) {
        features.push('EMA signal conditions');
    }
    if (supportedNodes.has('ta.crossover') || supportedNodes.has('ta.crossunder')) {
        features.push('Crossover and crossunder signal triggers');
    }

    return features;
}
