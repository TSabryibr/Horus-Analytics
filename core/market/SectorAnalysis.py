"""
SECTOR ANALYSIS MODULE
======================
Maps EGX stocks to their respective sectors and identifies hot sectors.
"""

from core.market import MarketLists

def get_sector(ticker):
    """
    Get sector for a ticker using dynamic MarketLists metadata.
    """
    return MarketLists.get_sector(ticker)

def get_hot_sectors(signals):
    """
    Given a list of signals (from DailyScanner), count which sectors have the most activity.
    """
    sector_counts = {}
    for s in signals:
        sector = get_sector(s['Ticker'])
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
    
    # Sort by count
    sorted_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_sectors
