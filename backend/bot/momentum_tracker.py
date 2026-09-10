"""
Intraday Momentum Tracking Module
Identifies strongest stocks in real-time
"""
import requests
from datetime import datetime, timedelta

class MomentumTracker:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers
        self.momentum_cache = {}
        self.market_open_prices = {}
    
    def get_intraday_performance(self, symbol):
        """Get stock's performance since market open"""
        try:
            # Get today's bars
            now = datetime.now()
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            
            url = f'https://data.alpaca.markets/v2/stocks/{symbol}/bars'
            params = {
                'timeframe': '1Min',
                'start': market_open.isoformat() + 'Z',
                'end': now.isoformat() + 'Z',
                'limit': 1000
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            
            if response.status_code != 200:
                return None
            
            bars = response.json().get('bars', [])
            
            if not bars or len(bars) < 2:
                return None
            
            open_price = float(bars[0]['o'])
            current_price = float(bars[-1]['c'])
            high_price = max(float(b['h']) for b in bars)
            low_price = min(float(b['l']) for b in bars)
            
            # Calculate metrics
            day_change_pct = ((current_price - open_price) / open_price) * 100
            high_from_open_pct = ((high_price - open_price) / open_price) * 100
            current_from_high_pct = ((current_price - high_price) / high_price) * 100
            
            # Volume profile
            total_volume = sum(float(b['v']) for b in bars)
            recent_volume = sum(float(b['v']) for b in bars[-30:])  # Last 30 minutes
            volume_acceleration = (recent_volume / 30) / (total_volume / len(bars)) if total_volume > 0 else 1
            
            return {
                'day_change_pct': day_change_pct,
                'high_from_open_pct': high_from_open_pct,
                'current_from_high_pct': current_from_high_pct,
                'volume_acceleration': volume_acceleration,
                'bars_count': len(bars)
            }
            
        except Exception as e:
            print(f"Error getting momentum for {symbol}: {e}")
            return None
    
    def calculate_momentum_score(self, symbol):
        """Calculate momentum score (0-100)"""
        perf = self.get_intraday_performance(symbol)
        
        if not perf:
            return 50  # Neutral if no data
        
        score = 50  # Start neutral
        
        # Day performance (up to 30 points)
        if perf['day_change_pct'] > 3:
            score += 30
        elif perf['day_change_pct'] > 1.5:
            score += 20
        elif perf['day_change_pct'] > 0.5:
            score += 10
        elif perf['day_change_pct'] < -1.5:
            score -= 20
        elif perf['day_change_pct'] < -0.5:
            score -= 10
        
        # Relative to high (up to 20 points)
        # Prefer stocks near highs
        if perf['current_from_high_pct'] > -1:
            score += 20  # At or near high
        elif perf['current_from_high_pct'] > -2:
            score += 10
        elif perf['current_from_high_pct'] < -5:
            score -= 15  # Far from high
        
        # Volume acceleration (up to 20 points)
        if perf['volume_acceleration'] > 1.5:
            score += 20  # Accelerating volume
        elif perf['volume_acceleration'] > 1.2:
            score += 10
        elif perf['volume_acceleration'] < 0.8:
            score -= 10  # Declining volume
        
        return max(0, min(100, score))
    
    def is_momentum_leader(self, symbol):
        """Check if stock is a momentum leader"""
        score = self.calculate_momentum_score(symbol)
        return score >= 70
    
    def is_momentum_laggard(self, symbol):
        """Check if stock is a momentum laggard"""
        score = self.calculate_momentum_score(symbol)
        return score <= 30
    
    def adjust_confidence_for_momentum(self, base_confidence, symbol):
        """Adjust confidence based on intraday momentum"""
        score = self.calculate_momentum_score(symbol)
        
        if score >= 80:
            # Strong momentum leader
            adjustment = 15
        elif score >= 70:
            # Good momentum
            adjustment = 8
        elif score <= 30:
            # Weak momentum - avoid
            adjustment = -20
        elif score <= 40:
            # Below average momentum
            adjustment = -10
        else:
            # Neutral
            adjustment = 0
        
        adjusted = base_confidence + adjustment
        return max(0, min(100, adjusted))
    
    def get_top_momentum_stocks(self, symbols, limit=20):
        """Get top momentum stocks from a list"""
        momentum_scores = []
        
        for symbol in symbols:
            score = self.calculate_momentum_score(symbol)
            momentum_scores.append({
                'symbol': symbol,
                'momentum_score': score
            })
        
        # Sort by momentum score
        momentum_scores.sort(key=lambda x: x['momentum_score'], reverse=True)
        
        return momentum_scores[:limit]
