"""
Advanced Market Regime Detection
"""
import requests
from datetime import datetime, timedelta

class MarketRegimeDetector:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers
        self.current_regime = 'neutral'
        self.regime_confidence = 0
    
    def get_bars(self, symbol, timeframe='1Day', limit=50):
        try:
            end = datetime.now()
            start = end - timedelta(days=100)
            url = f'https://data.alpaca.markets/v2/stocks/{symbol}/bars'
            params = {
                'timeframe': timeframe,
                'start': start.isoformat() + 'Z',
                'end': end.isoformat() + 'Z',
                'limit': limit
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            data = response.json()
            return data.get('bars', [])
        except:
            return []
    
    def detect_regime(self):
        try:
            spy_bars = self.get_bars('SPY', timeframe='1Day', limit=50)
            if not spy_bars or len(spy_bars) < 50:
                return 'neutral', 50
            closes = [float(bar['c']) for bar in spy_bars]
            current_price = closes[-1]
            sma_20 = sum(closes[-20:]) / 20
            sma_50 = sum(closes[-50:]) / 50
            bull_score = 0
            if current_price > sma_20 > sma_50:
                bull_score += 50
            if current_price > sma_20:
                bull_score += 25
            bear_score = 0
            if current_price < sma_20 < sma_50:
                bear_score += 50
            if current_price < sma_20:
                bear_score += 25
            if bull_score > 60:
                regime = 'bull'
                confidence = bull_score
            elif bear_score > 60:
                regime = 'bear'
                confidence = bear_score
            else:
                regime = 'neutral'
                confidence = 50
            self.current_regime = regime
            self.regime_confidence = confidence
            return regime, confidence
        except Exception as e:
            return 'neutral', 50
    
    def get_strategy_adjustments(self):
        regime, confidence = self.detect_regime()
        if regime == 'bull' and confidence > 70:
            return {'position_size_multiplier': 1.2, 'max_positions': 12, 'confidence_threshold': 65}
        elif regime == 'bear':
            return {'position_size_multiplier': 0.5, 'max_positions': 5, 'confidence_threshold': 80}
        elif regime == 'choppy':
            return {'position_size_multiplier': 0.7, 'max_positions': 7, 'confidence_threshold': 75}
        else:
            return {'position_size_multiplier': 1.0, 'max_positions': 10, 'confidence_threshold': 70}
