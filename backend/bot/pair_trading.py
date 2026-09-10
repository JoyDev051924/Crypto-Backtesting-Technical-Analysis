"""
Pair Trading Module
Trade correlated pairs for market-neutral profits
"""

class PairTrader:
    def __init__(self):
        # Define trading pairs (correlated stocks)
        self.pairs = [
            ('AAPL', 'MSFT'),   # Tech giants
            ('QQQ', 'SPY'),     # Nasdaq vs S&P
            ('XOM', 'CVX'),     # Oil majors
            ('JPM', 'BAC'),     # Big banks
            ('KO', 'PEP'),      # Beverages
            ('NVDA', 'AMD'),    # GPU makers
            ('GOOGL', 'META'),  # Ad platforms
        ]
        
        self.pair_positions = {}
    
    def calculate_spread(self, price1, price2, hist_prices1, hist_prices2):
        """Calculate z-score of price spread"""
        # Calculate historical ratio
        ratios = [h1/h2 for h1, h2 in zip(hist_prices1, hist_prices2)]
        avg_ratio = sum(ratios) / len(ratios)
        std_ratio = (sum((r - avg_ratio)**2 for r in ratios) / len(ratios)) ** 0.5
        
        # Current ratio
        current_ratio = price1 / price2
        
        # Z-score
        z_score = (current_ratio - avg_ratio) / std_ratio if std_ratio > 0 else 0
        
        return z_score
    
    def find_pair_opportunity(self, symbol1, symbol2, price1, price2, hist1, hist2):
        """Check if pair trade opportunity exists"""
        z_score = self.calculate_spread(price1, price2, hist1, hist2)
        
        # If z-score > 2: symbol1 overvalued vs symbol2
        # Action: SHORT symbol1, LONG symbol2
        if z_score > 2:
            return 'short_long', abs(z_score)
        
        # If z-score < -2: symbol1 undervalued vs symbol2
        # Action: LONG symbol1, SHORT symbol2
        elif z_score < -2:
            return 'long_short', abs(z_score)
        
        return None, 0
    
    def should_close_pair(self, z_score):
        """Check if pair trade should be closed (mean reversion)"""
        # Close when spread returns to normal (z-score near 0)
        return abs(z_score) < 0.5
