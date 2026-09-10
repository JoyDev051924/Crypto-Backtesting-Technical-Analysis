"""
OPTIONS TRADING MODULE
Handles options trading with 20% portfolio allocation
Only trades highest confidence setups (85%+)
"""

import requests
from datetime import datetime, timedelta

class OptionsTrader:
    def __init__(self, base_url, headers, cash_allocation=0.20):
        self.base_url = base_url
        self.headers = headers
        self.cash_allocation = cash_allocation  # 20% of portfolio
        self.min_confidence = 85  # Only trade 85%+ confidence
        self.max_positions = 3  # Max 3 option positions at once
        self.profit_target = 0.50  # Take profit at 50%
        self.stop_loss = 0.30  # Stop loss at -30%
        
    def get_option_chain(self, symbol):
        """Get available options for a symbol"""
        try:
            # Get options chain from Alpaca
            url = f'{self.base_url}/v2/options/contracts'
            params = {
                'underlying_symbol': symbol,
                'status': 'active',
                'expiration_date_gte': datetime.now().strftime('%Y-%m-%d'),
                'expiration_date_lte': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'type': 'call'  # Only calls for now
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json().get('option_contracts', [])
            return []
        except Exception as e:
            print(f"Error getting options chain: {e}")
            return []
    
    def find_best_option(self, symbol, current_price, confidence):
        """Find the best option contract to trade"""
        options = self.get_option_chain(symbol)
        
        if not options:
            return None
        
        # Look for slightly OTM calls (2-5% above current price)
        target_strike = current_price * 1.03  # 3% OTM
        
        best_option = None
        min_diff = float('inf')
        
        for option in options:
            strike = float(option.get('strike_price', 0))
            diff = abs(strike - target_strike)
            
            if diff < min_diff:
                min_diff = diff
                best_option = option
        
        return best_option
    
    def should_trade_options(self, symbol, confidence, current_positions):
        """Determine if we should trade options for this symbol"""
        # Only trade if confidence is very high
        if confidence < self.min_confidence:
            return False
        
        # Don't exceed max positions
        if len(current_positions) >= self.max_positions:
            return False
        
        # Check if options are available
        options = self.get_option_chain(symbol)
        if not options:
            return False
        
        return True
    
    def calculate_position_size(self, available_cash, option_price):
        """Calculate how many contracts to buy"""
        # Use allocated cash for options
        max_spend = available_cash * self.cash_allocation
        
        # Each contract controls 100 shares
        contract_cost = option_price * 100
        
        # Calculate number of contracts
        num_contracts = int(max_spend / contract_cost)
        
        # Limit to reasonable size
        return min(num_contracts, 10)
    
    def get_option_quote(self, option_symbol):
        """Get current price for an option"""
        try:
            url = f'{self.base_url}/v2/options/quotes/latest'
            params = {'symbols': option_symbol}
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if 'quotes' in data and option_symbol in data['quotes']:
                    quote = data['quotes'][option_symbol]
                    # Use mid price (average of bid/ask)
                    bid = float(quote.get('bid_price', 0))
                    ask = float(quote.get('ask_price', 0))
                    return (bid + ask) / 2 if bid and ask else None
            return None
        except Exception as e:
            print(f"Error getting option quote: {e}")
            return None
    
    def place_option_order(self, option_symbol, quantity, side='buy'):
        """Place an options order"""
        try:
            order_data = {
                'symbol': option_symbol,
                'qty': quantity,
                'side': side,
                'type': 'market',
                'time_in_force': 'day',
                'order_class': 'simple'
            }
            
            response = requests.post(
                f'{self.base_url}/v2/orders',
                headers=self.headers,
                json=order_data
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Order failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error placing option order: {e}")
            return None
    
    def check_option_positions(self, positions):
        """Check existing option positions for profit/loss targets"""
        positions_to_close = []
        
        for symbol, position in positions.items():
            current_price = self.get_option_quote(symbol)
            if not current_price:
                continue
            
            entry_price = position['entry_price']
            pnl_pct = (current_price - entry_price) / entry_price
            
            # Take profit at 50%
            if pnl_pct >= self.profit_target:
                positions_to_close.append((symbol, current_price, 'profit_target'))
                print(f"💰 OPTIONS PROFIT: {symbol} +{pnl_pct*100:.1f}%")
            
            # Stop loss at -30%
            elif pnl_pct <= -self.stop_loss:
                positions_to_close.append((symbol, current_price, 'stop_loss'))
                print(f"🛑 OPTIONS STOP: {symbol} {pnl_pct*100:.1f}%")
        
        return positions_to_close
