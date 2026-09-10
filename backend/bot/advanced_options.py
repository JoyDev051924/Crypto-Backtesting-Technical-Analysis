"""
Advanced Options Strategies
Includes spreads, covered calls, and iron condors
"""
from bot.options_module import OptionsTrader

class AdvancedOptionsTrader(OptionsTrader):
    def __init__(self, base_url, headers, cash_allocation=0.30):
        super().__init__(base_url, headers, cash_allocation)
        self.enable_spreads = True
        self.enable_covered_calls = True
        self.covered_calls_active = {}  # Track covered calls sold
    
    def can_sell_covered_call(self, symbol, stock_position, current_price):
        """Check if we can sell a covered call on a stock position"""
        if not self.enable_covered_calls:
            return False
        
        # Need at least 100 shares
        if stock_position['quantity'] < 100:
            return False
        
        # Stock should be in profit or flat (at least +2%)
        entry_price = stock_position['entry_price']
        profit_pct = (current_price - entry_price) / entry_price
        
        if profit_pct < 0.02:  # Must be up at least 2%
            return False
        
        # Don't sell covered call if already have one
        if symbol in self.covered_calls_active:
            return False
        
        return True
    
    def sell_covered_call(self, symbol, stock_price, quantity):
        """Sell a covered call to generate income"""
        try:
            # Find call option 5-7% OTM, expiring in 1-2 weeks
            target_strike = stock_price * 1.06  # 6% above current
            
            # This is simplified - in production would use actual options chain
            # For now, estimate premium at ~2-3% of stock price
            estimated_premium = stock_price * 0.025  # 2.5% premium
            num_contracts = quantity // 100
            
            if num_contracts < 1:
                return None
            
            # Record covered call
            self.covered_calls_active[symbol] = {
                'contracts': num_contracts,
                'strike': target_strike,
                'premium': estimated_premium,
                'sold_at': stock_price
            }
            
            return estimated_premium * num_contracts * 100
            
        except Exception as e:
            print(f"Error selling covered call for {symbol}: {e}")
            return None
    
    def can_sell_covered_call(self, symbol, stock_position):
        """Check if we can sell a covered call on a stock position"""
        if not self.enable_covered_calls:
            return False
        
        # Need at least 100 shares
        if stock_position['quantity'] < 100:
            return False
        
        # Stock should be in profit or flat
        current_price = stock_position.get('current_price', 0)
        entry_price = stock_position['entry_price']
        
        if current_price < entry_price * 0.98:  # Down more than 2%
            return False
        
        return True
    
    def find_covered_call(self, symbol, stock_price, stock_position):
        """Find best covered call to sell"""
        try:
            # Look for calls 5-10% OTM, expiring in 1-2 weeks
            target_strike = stock_price * 1.07  # 7% OTM
            
            option = self.find_best_option(symbol, stock_price, 85, call_put='call')
            
            if option and float(option['strike_price']) > stock_price * 1.05:
                return option
            
            return None
        except:
            return None
    
    def create_vertical_spread(self, symbol, stock_price, confidence, spread_type='call'):
        """Create a vertical spread (buy lower strike, sell higher strike)"""
        try:
            if spread_type == 'call':
                # Bull call spread
                # Buy ATM call
                buy_strike = stock_price * 1.02
                # Sell OTM call
                sell_strike = stock_price * 1.08
            else:
                # Bear put spread (not implemented yet)
                return None
            
            # For now, just use regular calls
            # Full spread implementation would require multiple orders
            return self.find_best_option(symbol, stock_price, confidence)
            
        except:
            return None
