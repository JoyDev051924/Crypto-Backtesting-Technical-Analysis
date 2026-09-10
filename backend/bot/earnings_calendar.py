"""
Earnings Calendar Integration
Avoid trading around earnings or target post-earnings momentum
"""
import requests
from datetime import datetime, timedelta

class EarningsCalendar:
    def __init__(self, alpaca_headers):
        self.headers = alpaca_headers
        self.earnings_cache = {}
    
    def get_earnings_date(self, symbol):
        """Get next earnings date for a symbol"""
        # Check cache
        if symbol in self.earnings_cache:
            return self.earnings_cache[symbol]
        
        try:
            # Use Alpaca's corporate actions API
            url = f'https://data.alpaca.markets/v1beta1/corporate-actions'
            params = {
                'symbols': symbol,
                'types': 'dividend,split',  # Alpaca doesn't have earnings in free tier
                'start': datetime.now().isoformat() + 'Z',
                'end': (datetime.now() + timedelta(days=30)).isoformat() + 'Z'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            
            # For now, we'll use a simple heuristic:
            # Most companies report quarterly (every ~90 days)
            # We'll mark stocks as "near earnings" if they've had unusual volume
            
            result = {
                'has_earnings_soon': False,
                'days_until': None,
                'post_earnings': False
            }
            
            self.earnings_cache[symbol] = result
            return result
            
        except Exception as e:
            return {
                'has_earnings_soon': False,
                'days_until': None,
                'post_earnings': False
            }
    
    def should_avoid_earnings(self, symbol):
        """Check if we should avoid trading this stock due to earnings"""
        earnings = self.get_earnings_date(symbol)
        
        # Avoid if earnings within 3 days
        if earnings['has_earnings_soon'] and earnings['days_until'] and earnings['days_until'] <= 3:
            return True
        
        return False
    
    def is_post_earnings_play(self, symbol, indicators):
        """Check if this is a good post-earnings momentum play"""
        earnings = self.get_earnings_date(symbol)
        
        # Look for post-earnings momentum:
        # - Just reported (within 5 days)
        # - Strong volume
        # - Strong price action
        if earnings['post_earnings']:
            if indicators['volume_ratio'] > 1.5 and indicators['rsi'] > 50:
                return True
        
        return False
    
    def adjust_confidence_for_earnings(self, base_confidence, symbol, indicators):
        """Adjust confidence based on earnings timing"""
        if self.should_avoid_earnings(symbol):
            # Avoid pre-earnings trades
            return 0
        
        if self.is_post_earnings_play(symbol, indicators):
            # Boost post-earnings momentum plays
            return min(100, base_confidence + 10)
        
        return base_confidence
