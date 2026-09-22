def analyze_bar(bar):
    """
    Receives a live bar from the Sentinel and checks for signals.
    
    Args:
        bar (dict): {'ticker': 'COMI', 'close': 50.5, ...}
    """
    price = bar['close']
    volume = bar['volume']
    
    print(f"\n[SIGNAL DETECTOR] New Data for {bar['ticker']} at {bar['timestamp']}")
    print(f" > Price: {price} | Vol: {volume}")
    
    # Mock Strategy Logic
    # Example: If price ends in .00, Buy. If .50, Sell.
    decimal = price % 1
    
    if decimal == 0.00:
        print(f" >>> 🟢 BUY SIGNAL DETECTED for {bar['ticker']} @ {price}")
    elif decimal == 0.50:
        print(f" >>> 🔴 SELL SIGNAL DETECTED for {bar['ticker']} @ {price}")
    else:
        print(" > No signal.")
