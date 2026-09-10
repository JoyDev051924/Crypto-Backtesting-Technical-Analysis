"""
Adaptive Position Sizing Module
Adjusts position sizes based on recent performance
"""
import json
from datetime import datetime, timedelta

class AdaptiveSizing:
    def __init__(self, state_file='bot/adaptive_sizing_state.json'):
        self.state_file = state_file
        self.recent_trades = []
        self.performance_multiplier = 1.0
        self.load_state()
    
    def load_state(self):
        """Load adaptive sizing state"""
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                self.recent_trades = data.get('recent_trades', [])
                self.performance_multiplier = data.get('performance_multiplier', 1.0)
        except FileNotFoundError:
            pass
    
    def save_state(self):
        """Save adaptive sizing state"""
        with open(self.state_file, 'w') as f:
            json.dump({
                'recent_trades': self.recent_trades,
                'performance_multiplier': self.performance_multiplier
            }, f, indent=2)
    
    def record_trade(self, pnl_pct, exit_time):
        """Record a completed trade"""
        self.recent_trades.append({
            'pnl_pct': pnl_pct,
            'exit_time': exit_time
        })
        
        # Keep only last 20 trades
        self.recent_trades = self.recent_trades[-20:]
        
        # Recalculate performance multiplier
        self.update_multiplier()
        self.save_state()
    
    def update_multiplier(self):
        """Update position size multiplier based on recent performance"""
        if len(self.recent_trades) < 5:
            # Not enough data
            self.performance_multiplier = 1.0
            return
        
        # Calculate recent win rate and average return
        recent_10 = self.recent_trades[-10:]
        wins = sum(1 for t in recent_10 if t['pnl_pct'] > 0)
        win_rate = wins / len(recent_10)
        avg_return = sum(t['pnl_pct'] for t in recent_10) / len(recent_10)
        
        # Adjust multiplier based on performance
        if win_rate >= 0.7 and avg_return > 2.0:
            # Hot streak - increase size by 30%
            self.performance_multiplier = 1.3
        elif win_rate >= 0.6 and avg_return > 1.0:
            # Good performance - increase size by 15%
            self.performance_multiplier = 1.15
        elif win_rate >= 0.5 and avg_return > 0:
            # Neutral - normal size
            self.performance_multiplier = 1.0
        elif win_rate < 0.4 or avg_return < -1.0:
            # Cold streak - reduce size by 40%
            self.performance_multiplier = 0.6
        else:
            # Slightly underperforming - reduce size by 20%
            self.performance_multiplier = 0.8
        
        # Cap multiplier between 0.5 and 1.5
        self.performance_multiplier = max(0.5, min(1.5, self.performance_multiplier))
    
    def get_size_multiplier(self):
        """Get current position size multiplier"""
        return self.performance_multiplier
    
    def get_performance_summary(self):
        """Get summary of recent performance"""
        if len(self.recent_trades) < 5:
            return {
                'status': 'insufficient_data',
                'multiplier': 1.0,
                'trades': len(self.recent_trades)
            }
        
        recent_10 = self.recent_trades[-10:]
        wins = sum(1 for t in recent_10 if t['pnl_pct'] > 0)
        win_rate = wins / len(recent_10)
        avg_return = sum(t['pnl_pct'] for t in recent_10) / len(recent_10)
        
        if win_rate >= 0.6:
            status = 'hot_streak'
        elif win_rate >= 0.5:
            status = 'normal'
        else:
            status = 'cold_streak'
        
        return {
            'status': status,
            'multiplier': self.performance_multiplier,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'recent_trades': len(recent_10)
        }
