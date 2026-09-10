"""
Machine Learning Pattern Recognition Module
Learns from historical trades to improve confidence scoring
"""
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

class MLPredictor:
    def __init__(self, state_file='bot/ml_model_state.json'):
        self.state_file = state_file
        self.pattern_performance = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total_return': 0})
        self.load_state()
    
    def load_state(self):
        """Load learned patterns from file"""
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                self.pattern_performance = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total_return': 0}, data)
        except FileNotFoundError:
            pass
    
    def save_state(self):
        """Save learned patterns to file"""
        with open(self.state_file, 'w') as f:
            json.dump(dict(self.pattern_performance), f, indent=2)
    
    def get_pattern_key(self, indicators, regime):
        """Create a pattern key from indicators"""
        # Discretize indicators into buckets for pattern matching
        rsi_bucket = 'low' if indicators['rsi'] < 40 else 'mid' if indicators['rsi'] < 60 else 'high'
        macd_bucket = 'bullish' if indicators['macd_histogram'] > 0 else 'bearish'
        volume_bucket = 'high' if indicators['volume_ratio'] > 1.2 else 'normal'
        trend_bucket = 'strong' if indicators['price'] > indicators['sma_20'] > indicators['sma_50'] else 'weak'
        
        return f"{regime}_{rsi_bucket}_{macd_bucket}_{volume_bucket}_{trend_bucket}"
    
    def adjust_confidence(self, base_confidence, indicators, regime):
        """Adjust confidence based on learned patterns"""
        pattern_key = self.get_pattern_key(indicators, regime)
        pattern_stats = self.pattern_performance[pattern_key]
        
        total_trades = pattern_stats['wins'] + pattern_stats['losses']
        
        if total_trades < 5:
            # Not enough data, use base confidence
            return base_confidence
        
        # Calculate win rate and average return
        win_rate = pattern_stats['wins'] / total_trades
        avg_return = pattern_stats['total_return'] / total_trades
        
        # Adjust confidence based on historical performance
        # Win rate > 60% = boost confidence
        # Win rate < 40% = reduce confidence
        adjustment = 0
        
        if win_rate > 0.6 and avg_return > 0.03:
            adjustment = 10  # Strong pattern, boost confidence
        elif win_rate > 0.5 and avg_return > 0.01:
            adjustment = 5   # Good pattern, slight boost
        elif win_rate < 0.4 or avg_return < -0.01:
            adjustment = -15  # Bad pattern, reduce confidence
        elif win_rate < 0.5:
            adjustment = -5   # Weak pattern, slight reduction
        
        adjusted = base_confidence + adjustment
        return max(0, min(100, adjusted))
    
    def record_trade_result(self, indicators, regime, pnl_pct):
        """Record trade result to learn from"""
        pattern_key = self.get_pattern_key(indicators, regime)
        
        if pnl_pct > 0:
            self.pattern_performance[pattern_key]['wins'] += 1
        else:
            self.pattern_performance[pattern_key]['losses'] += 1
        
        self.pattern_performance[pattern_key]['total_return'] += pnl_pct / 100
        
        self.save_state()
    
    def get_pattern_stats(self):
        """Get statistics on learned patterns"""
        stats = []
        for pattern, data in self.pattern_performance.items():
            total = data['wins'] + data['losses']
            if total > 0:
                win_rate = data['wins'] / total
                avg_return = data['total_return'] / total
                stats.append({
                    'pattern': pattern,
                    'trades': total,
                    'win_rate': win_rate,
                    'avg_return': avg_return
                })
        
        return sorted(stats, key=lambda x: x['trades'], reverse=True)
