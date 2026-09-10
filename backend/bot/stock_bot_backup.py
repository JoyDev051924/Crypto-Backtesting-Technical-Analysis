import os
import time
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bot.options_module import OptionsTrader

load_dotenv()

class StockTradingBot:
    def __init__(self):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_API_SECRET')
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        self.headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret
        }
        
        # Trading parameters
        self.symbols = []  # Will be populated dynamically
        self.base_position_size = 0.05  # Base 5% per position
        self.max_position_size = 0.15  # Max 15% for high confidence trades
        self.max_positions = 10  # Up to 10 positions for diversification
        self.stop_loss_pct = 0.04  # 4% stop loss
        self.partial_profit_pct = 0.04  # Take 50% profit at 4%
        self.take_profit_pct = 0.08  # 8% full take profit
        self.trailing_stop_pct = 0.03  # 3% trailing stop after profit
        self.confidence_threshold = 0.70  # 70% confidence to enter
        
        # Trading hours restrictions
        self.market_open_buffer = 30  # Wait 30 min after open
        self.market_close_buffer = 60  # Stop trading 60 min before close
        self.close_all_eod = True  # Close all positions before market close
        
        # Risk management
        self.daily_loss_limit = 0.05  # Stop trading if down 5% in a day
        self.max_drawdown = 0.10  # Pause if down 10% from peak
        self.max_sector_exposure = 0.30  # Max 30% in one sector
        self.high_vix_threshold = 25  # Reduce size if VIX > 25
        
        # State tracking
        self.starting_daily_value = None
        self.peak_portfolio_value = 100000
        self.is_paused = False
        
        # State management
        self.state_file = 'bot/stock_bot_state.json'
        self.log_file = 'bot/stock_bot_log.json'
        self.load_state()
        
        # Initialize options trader (20% allocation)
        self.options_trader = OptionsTrader(self.base_url, self.headers, cash_allocation=0.20)
        self.options_positions = {}  # Separate tracking for options
        self.options_enabled = True  # Can disable if needed
        
    def load_state(self):
        """Load bot state from file"""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                self.cash = state.get('cash', 100000)
                self.positions = state.get('positions', {})
                self.trades = state.get('trades', [])
                self.started_at = state.get('started_at', datetime.now().isoformat())
                self.peak_portfolio_value = state.get('peak_portfolio_value', 100000)
                self.is_paused = state.get('is_paused', False)
                self.options_positions = state.get('options_positions', {})
        except FileNotFoundError:
            self.cash = 100000  # Alpaca paper trading default
            self.positions = {}
            self.trades = []
            self.started_at = datetime.now().isoformat()
            self.peak_portfolio_value = 100000
            self.is_paused = False
            self.options_positions = {}
            self.save_state()
    
    def save_state(self):
        """Save bot state to file"""
        state = {
            'cash': self.cash,
            'positions': self.positions,
            'trades': self.trades,
            'started_at': self.started_at,
            'total_pnl': sum(t['pnl'] for t in self.trades),
            'wins': len([t for t in self.trades if t['pnl'] > 0]),
            'losses': len([t for t in self.trades if t['pnl'] < 0]),
            'peak_portfolio_value': self.peak_portfolio_value,
            'is_paused': self.is_paused,
            'options_positions': self.options_positions
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def log_event(self, event_type, data):
        """Log events to file"""
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
        except FileNotFoundError:
            logs = []
        
        logs.append({
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        })
        
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)

    
    def get_account(self):
        """Get account information"""
        response = requests.get(f'{self.base_url}/v2/account', headers=self.headers)
        return response.json()
    
    def get_vix(self):
        """Get VIX (volatility index) value"""
        try:
            bars = self.get_bars('VIX', limit=1)
            if bars:
                return float(bars[-1]['c'])
        except:
            pass
        return 15  # Default to normal volatility
    
    def get_sector_exposure(self):
        """Calculate current sector exposure"""
        # Simplified sector mapping
        sector_map = {
            'tech': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'AMD', 'INTC', 'NFLX', 'CRM', 'ORCL', 'ADBE', 'QCOM', 'TSLA'],
            'finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'V', 'MA'],
            'healthcare': ['UNH', 'JNJ', 'LLY', 'ABT', 'PFE', 'DHR', 'BMY', 'AMGN', 'GILD', 'MRK', 'ABBV'],
            'consumer': ['WMT', 'PG', 'KO', 'PEP', 'COST', 'MCD', 'DIS', 'NKE', 'SBUX', 'TGT'],
            'energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC'],
            'industrial': ['BA', 'CAT', 'GE', 'UPS', 'HON', 'RTX', 'LMT']
        }
        
        sector_exposure = {}
        portfolio_value = self.get_portfolio_value()
        
        for symbol, position in self.positions.items():
            bars = self.get_bars(symbol, limit=1)
            if not bars:
                continue
            
            current_price = float(bars[-1]['c'])
            position_value = current_price * position['quantity']
            
            # Find sector
            sector = 'other'
            for s, symbols in sector_map.items():
                if symbol in symbols:
                    sector = s
                    break
            
            sector_exposure[sector] = sector_exposure.get(sector, 0) + position_value
        
        # Convert to percentages
        for sector in sector_exposure:
            sector_exposure[sector] = sector_exposure[sector] / portfolio_value if portfolio_value > 0 else 0
        
        return sector_exposure
    
    def check_sector_limit(self, symbol):
        """Check if adding this symbol would exceed sector limits"""
        sector_map = {
            'tech': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'AMD', 'INTC', 'NFLX', 'CRM', 'ORCL', 'ADBE', 'QCOM', 'TSLA'],
            'finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'V', 'MA'],
            'healthcare': ['UNH', 'JNJ', 'LLY', 'ABT', 'PFE', 'DHR', 'BMY', 'AMGN', 'GILD', 'MRK', 'ABBV'],
            'consumer': ['WMT', 'PG', 'KO', 'PEP', 'COST', 'MCD', 'DIS', 'NKE', 'SBUX', 'TGT'],
            'energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC'],
            'industrial': ['BA', 'CAT', 'GE', 'UPS', 'HON', 'RTX', 'LMT']
        }
        
        # Find symbol's sector
        symbol_sector = 'other'
        for sector, symbols in sector_map.items():
            if symbol in symbols:
                symbol_sector = sector
                break
        
        # Check current exposure
        sector_exposure = self.get_sector_exposure()
        current_exposure = sector_exposure.get(symbol_sector, 0)
        
        return current_exposure < self.max_sector_exposure
    
    def check_daily_loss_limit(self):
        """Check if daily loss limit has been hit"""
        if self.starting_daily_value is None:
            return False
        
        current_value = self.get_portfolio_value()
        daily_return = (current_value - self.starting_daily_value) / self.starting_daily_value
        
        if daily_return <= -self.daily_loss_limit:
            print(f"⚠️  DAILY LOSS LIMIT HIT: {daily_return*100:.2f}%")
            self.is_paused = True
            self.save_state()
            return True
        
        return False
    
    def check_max_drawdown(self):
        """Check if max drawdown has been exceeded"""
        current_value = self.get_portfolio_value()
        
        # Update peak
        if current_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_value
            self.save_state()
        
        # Check drawdown
        drawdown = (self.peak_portfolio_value - current_value) / self.peak_portfolio_value
        
        if drawdown >= self.max_drawdown:
            print(f"⚠️  MAX DRAWDOWN EXCEEDED: {drawdown*100:.2f}%")
            self.is_paused = True
            self.save_state()
            return True
        
        return False
    
    def get_liquid_stocks(self):
        """Get list of highly liquid stocks"""
        # Get all active assets
        response = requests.get(f'{self.base_url}/v2/assets', headers=self.headers, params={
            'status': 'active',
            'asset_class': 'us_equity'
        })
        
        if response.status_code != 200:
            print(f"Error fetching assets: {response.status_code}")
            return []
        
        assets = response.json()
        
        # Filter for tradable, liquid stocks
        liquid_stocks = []
        for asset in assets:
            # Must be tradable and not a fractional share
            if not asset.get('tradable', False):
                continue
            if not asset.get('fractionable', False):
                continue
            if asset.get('status') != 'active':
                continue
            
            symbol = asset.get('symbol', '')
            
            # Skip penny stocks and weird symbols
            if '.' in symbol or '-' in symbol or len(symbol) > 5:
                continue
            
            liquid_stocks.append(symbol)
        
        print(f"Found {len(liquid_stocks)} tradable stocks")
        
        # For now, return top stocks by market cap (we'll filter by volume later)
        # Focus on well-known liquid stocks
        priority_stocks = [
            # Major ETFs
            'SPY', 'QQQ', 'IWM', 'DIA', 'VOO', 'VTI',
            # Mega cap tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
            # Other mega caps
            'BRK.B', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'HD', 'CVX', 'MRK',
            'ABBV', 'KO', 'PEP', 'COST', 'AVGO', 'TMO', 'MCD', 'CSCO', 'ACN',
            # High volume tech/growth
            'AMD', 'INTC', 'NFLX', 'CRM', 'ORCL', 'ADBE', 'QCOM', 'TXN', 'AMAT',
            # Finance
            'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP',
            # Healthcare
            'UNH', 'LLY', 'ABT', 'PFE', 'DHR', 'BMY', 'AMGN', 'GILD',
            # Consumer
            'DIS', 'NKE', 'SBUX', 'TGT', 'LOW', 'BKNG', 'CMG',
            # Energy
            'XOM', 'COP', 'SLB', 'EOG', 'MPC',
            # Industrial
            'BA', 'CAT', 'GE', 'UPS', 'HON', 'RTX', 'LMT',
            # Telecom
            'T', 'VZ', 'TMUS',
            # Retail
            'AMZN', 'SHOP', 'EBAY', 'ETSY',
            # Semiconductors
            'TSM', 'ASML', 'MU', 'LRCX', 'KLAC', 'SNPS', 'CDNS',
            # Auto
            'F', 'GM', 'RIVN', 'LCID',
            # Biotech
            'MRNA', 'BNTX', 'REGN', 'VRTX', 'BIIB',
            # Crypto-related
            'COIN', 'MSTR', 'RIOT', 'MARA',
            # Meme stocks (if liquid)
            'GME', 'AMC', 'PLTR', 'SOFI', 'HOOD',
            # Chinese ADRs (high volume)
            'BABA', 'JD', 'PDD', 'NIO', 'XPEV', 'LI',
            # Other high volume
            'SNAP', 'UBER', 'LYFT', 'ABNB', 'DASH', 'SQ', 'PYPL',
            'ZM', 'DOCU', 'SNOW', 'DDOG', 'NET', 'CRWD', 'ZS',
            # Banks
            'USB', 'PNC', 'TFC', 'COF',
            # Pharma
            'NVO', 'AZN', 'SNY', 'GSK',
            # Materials
            'LIN', 'APD', 'SHW', 'NEM', 'FCX',
            # Utilities
            'NEE', 'DUK', 'SO', 'D',
            # REITs
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG',
        ]
        
        # Filter to only include stocks that exist in our tradable list
        available_priority = [s for s in priority_stocks if s in liquid_stocks]
        
        print(f"Monitoring {len(available_priority)} highly liquid stocks")
        return available_priority
    
    def get_bars(self, symbol, timeframe='1Min', limit=100):
        """Get historical price bars"""
        end = datetime.now()
        start = end - timedelta(days=5)
        
        url = f'https://data.alpaca.markets/v2/stocks/{symbol}/bars'
        params = {
            'timeframe': timeframe,
            'start': start.isoformat() + 'Z',
            'end': end.isoformat() + 'Z',
            'limit': limit
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        data = response.json()
        return data.get('bars', [])
    
    def calculate_indicators(self, bars):
        """Calculate technical indicators"""
        if len(bars) < 50:
            return None
        
        closes = [float(bar['c']) for bar in bars]
        highs = [float(bar['h']) for bar in bars]
        lows = [float(bar['l']) for bar in bars]
        volumes = [float(bar['v']) for bar in bars]
        
        # Moving averages
        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50
        
        # RSI
        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = closes[-1]
        ema_26 = sum(closes[-26:]) / 26
        macd = ema_12 - ema_26
        signal = sum(closes[-9:]) / 9
        macd_histogram = macd - signal
        
        # Bollinger Bands
        std_dev = (sum((x - sma_20) ** 2 for x in closes[-20:]) / 20) ** 0.5
        bb_upper = sma_20 + (2 * std_dev)
        bb_lower = sma_20 - (2 * std_dev)
        
        # Volume analysis
        avg_volume = sum(volumes[-20:]) / 20
        volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
        
        current_price = closes[-1]
        
        return {
            'price': current_price,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'rsi': rsi,
            'macd': macd,
            'macd_histogram': macd_histogram,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'volume_ratio': volume_ratio
        }
    
    def detect_market_regime(self, indicators):
        """Detect if market is in uptrend, downtrend, or ranging"""
        price = indicators['price']
        sma_20 = indicators['sma_20']
        sma_50 = indicators['sma_50']
        
        if price > sma_20 > sma_50:
            return 'uptrend'
        elif price < sma_20 < sma_50:
            return 'downtrend'
        else:
            return 'ranging'
    
    def calculate_confidence(self, indicators, regime):
        """Calculate confidence score for entry"""
        if regime != 'uptrend':
            return 0
        
        confidence = 0
        
        # Price above moving averages (30 points)
        if indicators['price'] > indicators['sma_20']:
            confidence += 15
        if indicators['sma_20'] > indicators['sma_50']:
            confidence += 15
        
        # RSI in good range (20 points)
        if 40 < indicators['rsi'] < 70:
            confidence += 20
        elif 30 < indicators['rsi'] < 80:
            confidence += 10
        
        # MACD bullish (20 points)
        if indicators['macd_histogram'] > 0:
            confidence += 20
        elif indicators['macd'] > 0:
            confidence += 10
        
        # Volume confirmation (15 points)
        if indicators['volume_ratio'] > 1.2:
            confidence += 15
        elif indicators['volume_ratio'] > 1.0:
            confidence += 8
        
        # Bollinger Band position (15 points)
        bb_position = (indicators['price'] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower'])
        if 0.3 < bb_position < 0.7:
            confidence += 15
        elif 0.2 < bb_position < 0.8:
            confidence += 8
        
        return confidence

    
    def place_order(self, symbol, qty, side='buy'):
        """Place a market order"""
        order_data = {
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'type': 'market',
            'time_in_force': 'day'
        }
        
        response = requests.post(
            f'{self.base_url}/v2/orders',
            headers=self.headers,
            json=order_data
        )
        
        return response.json()
    
    def check_positions(self):
        """Check and manage existing positions with improved exit logic"""
        for symbol, position in list(self.positions.items()):
            bars = self.get_bars(symbol, limit=10)
            if not bars:
                continue
            
            current_price = float(bars[-1]['c'])
            entry_price = position['entry_price']
            quantity = position['quantity']
            pnl_pct = (current_price - entry_price) / entry_price
            
            # Update highest price seen for trailing stop
            if 'highest_price' not in position:
                position['highest_price'] = current_price
            elif current_price > position['highest_price']:
                position['highest_price'] = current_price
                self.save_state()
            
            # Check stop loss (CRITICAL - must execute)
            if pnl_pct <= -self.stop_loss_pct:
                print(f"🛑 STOP LOSS triggered for {symbol}: {pnl_pct*100:.2f}%")
                self.close_position(symbol, current_price, 'stop_loss')
                self.log_event('stop_loss', {
                    'symbol': symbol,
                    'entry': entry_price,
                    'exit': current_price,
                    'pnl_pct': pnl_pct * 100
                })
                continue
            
            # Partial profit taking at 4% (NEW)
            if pnl_pct >= self.partial_profit_pct and not position.get('partial_taken', False):
                # Sell half the position
                partial_qty = quantity // 2
                if partial_qty > 0:
                    print(f"💰 PARTIAL PROFIT for {symbol}: Taking 50% at +{pnl_pct*100:.2f}%")
                    try:
                        self.place_order(symbol, partial_qty, side='sell')
                        
                        # Update position
                        position['quantity'] = quantity - partial_qty
                        position['partial_taken'] = True
                        self.cash += current_price * partial_qty
                        
                        # Record partial profit
                        partial_pnl = (current_price - entry_price) * partial_qty
                        self.trades.append({
                            'symbol': symbol,
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'quantity': partial_qty,
                            'pnl': partial_pnl,
                            'pnl_pct': pnl_pct * 100,
                            'reason': 'partial_profit',
                            'entry_time': position['entry_time'],
                            'exit_time': datetime.now().isoformat()
                        })
                        
                        self.save_state()
                        print(f"✅ Sold {partial_qty} shares, holding {position['quantity']}")
                    except Exception as e:
                        print(f"❌ Error taking partial profit: {e}")
                continue
            
            # Trailing stop (only if in profit and partial taken)
            if pnl_pct > 0 and position.get('partial_taken', False):
                trailing_stop_price = position['highest_price'] * (1 - self.trailing_stop_pct)
                if current_price <= trailing_stop_price:
                    print(f"📉 TRAILING STOP for {symbol}: Locking in profit")
                    self.close_position(symbol, current_price, 'trailing_stop')
                    self.log_event('trailing_stop', {
                        'symbol': symbol,
                        'entry': entry_price,
                        'exit': current_price,
                        'highest': position['highest_price'],
                        'pnl_pct': pnl_pct * 100
                    })
                    continue
            
            # Full take profit
            if pnl_pct >= self.take_profit_pct:
                print(f"🎯 TAKE PROFIT for {symbol}: +{pnl_pct*100:.2f}%")
                self.close_position(symbol, current_price, 'take_profit')
                self.log_event('take_profit', {
                    'symbol': symbol,
                    'entry': entry_price,
                    'exit': current_price,
                    'pnl_pct': pnl_pct * 100
                })
                continue
    
    def close_position(self, symbol, exit_price, reason):
        """Close a position with better error handling"""
        if symbol not in self.positions:
            print(f"⚠️  Position {symbol} not found")
            return
            
        position = self.positions[symbol]
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        try:
            # Place sell order with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    order = self.place_order(symbol, quantity, side='sell')
                    if order and order.get('status') != 'rejected':
                        break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"⚠️  Retry {attempt + 1}/{max_retries} for {symbol}")
                    time.sleep(1)
            
            # Calculate P&L
            pnl = (exit_price - entry_price) * quantity
            pnl_pct = (exit_price - entry_price) / entry_price * 100
            
            # Record trade
            self.trades.append({
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'reason': reason,
                'entry_time': position['entry_time'],
                'exit_time': datetime.now().isoformat()
            })
            
            # Update cash
            self.cash += exit_price * quantity
            
            # Remove position
            del self.positions[symbol]
            
            self.save_state()
            
            emoji = "✅" if pnl > 0 else "❌"
            print(f"{emoji} CLOSED {symbol}: {reason} | Entry: ${entry_price:.2f} | Exit: ${exit_price:.2f} | P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR closing {symbol}: {e}")
            # Log the error but don't crash
            self.log_event('close_error', {
                'symbol': symbol,
                'error': str(e),
                'reason': reason
            })
    
    def scan_for_entries(self):
        """Scan symbols for entry opportunities with safety checks"""
        # Check if paused
        if self.is_paused:
            print("⚠️  Bot is PAUSED due to risk limits")
            return
        
        # Check risk limits
        if self.check_daily_loss_limit() or self.check_max_drawdown():
            return
        
        if len(self.positions) >= self.max_positions:
            return
        
        # Get VIX for volatility adjustment
        vix = self.get_vix()
        volatility_multiplier = 1.0
        if vix > self.high_vix_threshold:
            volatility_multiplier = 0.7  # Reduce position sizes by 30%
            print(f"⚠️  High volatility detected (VIX: {vix:.1f}), reducing position sizes")
        
        for symbol in self.symbols:
            if symbol in self.positions:
                continue
            
            # Check sector limits
            if not self.check_sector_limit(symbol):
                continue
            
            try:
                bars = self.get_bars(symbol)
                if not bars:
                    continue
                
                indicators = self.calculate_indicators(bars)
                if not indicators:
                    continue
                
                regime = self.detect_market_regime(indicators)
                confidence = self.calculate_confidence(indicators, regime)
                
                if confidence >= self.confidence_threshold * 100:
                    # Check if we should trade options instead (high confidence only)
                    if (self.options_enabled and 
                        confidence >= 85 and 
                        self.options_trader.should_trade_options(symbol, confidence, self.options_positions)):
                        
                        # Try to trade options
                        self.enter_option_position(symbol, indicators['price'], confidence)
                    else:
                        # Trade stocks
                        self.enter_position(symbol, indicators['price'], confidence, volatility_multiplier)
                    
                    if len(self.positions) + len(self.options_positions) >= self.max_positions:
                        break
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
                continue
    
    def enter_position(self, symbol, price, confidence, volatility_multiplier=1.0):
        """Enter a new position with dynamic sizing based on confidence and volatility"""
        # Scale position size based on confidence (70-100%)
        confidence_normalized = (confidence - 70) / 30  # 0 to 1 scale
        position_size = self.base_position_size + (confidence_normalized * (self.max_position_size - self.base_position_size))
        position_size = max(self.base_position_size, min(self.max_position_size, position_size))
        
        # Adjust for volatility
        position_size *= volatility_multiplier
        
        position_value = self.cash * position_size
        quantity = int(position_value / price)
        
        if quantity < 1:
            return
        
        try:
            # Place buy order
            order = self.place_order(symbol, quantity, side='buy')
            
            # Verify order was filled
            if not order or order.get('status') == 'rejected':
                print(f"❌ Order rejected for {symbol}")
                return
            
            # Record position
            self.positions[symbol] = {
                'entry_price': price,
                'quantity': quantity,
                'entry_time': datetime.now().isoformat(),
                'confidence': confidence,
                'position_size': position_size,
                'highest_price': price,
                'order_id': order.get('id')
            }
            
            # Update cash
            self.cash -= price * quantity
            
            self.save_state()
            
            self.log_event('entry', {
                'symbol': symbol,
                'price': price,
                'quantity': quantity,
                'confidence': confidence,
                'position_size_pct': position_size * 100,
                'volatility_adjusted': volatility_multiplier < 1.0
            })
            
            print(f"✅ ENTERED {symbol}: ${price:.2f} x {quantity} shares | Confidence: {confidence:.0f}% | Size: {position_size*100:.1f}%")
        
        except Exception as e:
            print(f"❌ Error entering {symbol}: {e}")

    
    def is_market_open(self):
        """Check if market is currently open"""
        response = requests.get(f'{self.base_url}/v2/clock', headers=self.headers)
        clock = response.json()
        return clock.get('is_open', False)
    
    def is_trading_hours(self):
        """Check if we're in valid trading hours (not first/last hour)"""
        try:
            response = requests.get(f'{self.base_url}/v2/clock', headers=self.headers)
            clock = response.json()
            
            if not clock.get('is_open', False):
                return False, "market_closed"
            
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            
            # Parse market open/close times
            next_open = datetime.fromisoformat(clock['next_open'].replace('Z', '+00:00'))
            next_close = datetime.fromisoformat(clock['next_close'].replace('Z', '+00:00'))
            
            # If market just opened (within buffer minutes)
            minutes_since_open = (now - next_open).total_seconds() / 60
            if minutes_since_open < self.market_open_buffer:
                return False, "too_early"
            
            # If market closing soon (within buffer minutes)
            minutes_until_close = (next_close - now).total_seconds() / 60
            if minutes_until_close < self.market_close_buffer:
                return False, "too_late"
            
            return True, "ok"
        except:
            return False, "error"
    
    def should_close_all_positions(self):
        """Check if we should close all positions before market close"""
        try:
            response = requests.get(f'{self.base_url}/v2/clock', headers=self.headers)
            clock = response.json()
            
            if not clock.get('is_open', False):
                return False
            
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            next_close = datetime.fromisoformat(clock['next_close'].replace('Z', '+00:00'))
            
            # Close all positions 15 minutes before market close
            minutes_until_close = (next_close - now).total_seconds() / 60
            return minutes_until_close <= 15
        except:
            return False
    
    def get_portfolio_value(self):
        """Calculate total portfolio value"""
        total = self.cash
        
        for symbol, position in self.positions.items():
            bars = self.get_bars(symbol, limit=1)
            if bars:
                current_price = float(bars[-1]['c'])
                total += current_price * position['quantity']
        
        return total
    
    def run(self):
        """Main bot loop"""
        print("=" * 60)
        print("STOCK TRADING BOT STARTED")
        print("=" * 60)
        
        # Fetch liquid stocks
        self.symbols = self.get_liquid_stocks()
        
        print(f"Starting Capital: ${self.cash:,.2f}")
        print(f"Monitoring {len(self.symbols)} stocks")
        print(f"Max Positions: {self.max_positions}")
        print(f"Position Size: {self.base_position_size * 100}% - {self.max_position_size * 100}% (confidence-based)")
        print(f"Stop Loss: {self.stop_loss_pct * 100}%")
        print(f"Take Profit: {self.take_profit_pct * 100}%")
        print("=" * 60)
        
        while True:
            try:
                # Check if market is open
                if not self.is_market_open():
                    # Reset daily tracking at market close
                    self.starting_daily_value = None
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Market is closed. Waiting...")
                    time.sleep(300)  # Check every 5 minutes
                    continue
                
                # Check if we should close all positions before market close
                if self.close_all_eod and self.should_close_all_positions():
                    print("🔔 Market closing soon - closing all positions!")
                    for symbol in list(self.positions.keys()):
                        bars = self.get_bars(symbol, limit=1)
                        if bars:
                            current_price = float(bars[-1]['c'])
                            self.close_position(symbol, current_price, 'end_of_day')
                    print("✅ All positions closed for the day")
                    time.sleep(300)  # Wait until market closes
                    continue
                
                # Set starting daily value on first check of the day
                if self.starting_daily_value is None:
                    self.starting_daily_value = self.get_portfolio_value()
                    print(f"📊 Starting daily value: ${self.starting_daily_value:,.2f}")
                
                # Check existing positions
                self.check_positions()
                
                # Check options positions
                self.check_option_positions()
                
                # Check if we're in valid trading hours
                can_trade, reason = self.is_trading_hours()
                if can_trade:
                    # Scan for new entries (with all safety checks)
                    self.scan_for_entries()
                else:
                    if reason == "too_early":
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for market to stabilize (30 min buffer)...")
                    elif reason == "too_late":
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Too close to market close - no new entries")
                
                # Calculate portfolio value
                portfolio_value = self.get_portfolio_value()
                returns_pct = (portfolio_value - 100000) / 100000 * 100
                daily_returns_pct = (portfolio_value - self.starting_daily_value) / self.starting_daily_value * 100 if self.starting_daily_value else 0
                
                # Log cycle
                self.log_event('cycle', {
                    'total_value': portfolio_value,
                    'returns_pct': returns_pct,
                    'daily_returns_pct': daily_returns_pct,
                    'positions': len(self.positions),
                    'is_paused': self.is_paused,
                    'can_trade': can_trade
                })
                
                status = "⚠️ PAUSED" if self.is_paused else "✅ ACTIVE"
                trade_status = "🟢 TRADING" if can_trade else "🟡 MONITORING"
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {status} {trade_status} | Portfolio: ${portfolio_value:,.2f} | Total: {returns_pct:+.2f}% | Today: {daily_returns_pct:+.2f}% | Positions: {len(self.positions)}")
                
                # Wait before next cycle
                time.sleep(60)  # Check every 1 minute
                
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(60)

if __name__ == '__main__':
    bot = StockTradingBot()
    bot.run()

    
    def enter_option_position(self, symbol, stock_price, confidence):
        """Enter an options position (high confidence only)"""
        try:
            print(f"🎯 HIGH CONFIDENCE ({confidence:.0f}%) - Considering OPTIONS for {symbol}")
            
            # Find best option contract
            option = self.options_trader.find_best_option(symbol, stock_price, confidence)
            if not option:
                print(f"⚠️  No suitable options found for {symbol}, trading stock instead")
                self.enter_position(symbol, stock_price, confidence, 1.0)
                return
            
            option_symbol = option['symbol']
            
            # Get option price
            option_price = self.options_trader.get_option_quote(option_symbol)
            if not option_price:
                print(f"⚠️  Can't get option price for {symbol}, trading stock instead")
                self.enter_position(symbol, stock_price, confidence, 1.0)
                return
            
            # Calculate position size
            num_contracts = self.options_trader.calculate_position_size(self.cash, option_price)
            if num_contracts < 1:
                print(f"⚠️  Not enough cash for options on {symbol}")
                return
            
            # Place order
            order = self.options_trader.place_option_order(option_symbol, num_contracts, side='buy')
            if not order or order.get('status') == 'rejected':
                print(f"❌ Options order rejected for {symbol}")
                return
            
            # Record position
            cost = option_price * num_contracts * 100  # Each contract = 100 shares
            self.options_positions[option_symbol] = {
                'underlying': symbol,
                'entry_price': option_price,
                'contracts': num_contracts,
                'entry_time': datetime.now().isoformat(),
                'confidence': confidence,
                'strike': float(option['strike_price']),
                'expiration': option['expiration_date'],
                'order_id': order.get('id')
            }
            
            # Update cash
            self.cash -= cost
            self.save_state()
            
            self.log_event('options_entry', {
                'symbol': option_symbol,
                'underlying': symbol,
                'price': option_price,
                'contracts': num_contracts,
                'confidence': confidence,
                'cost': cost
            })
            
            print(f"✅ OPTIONS ENTERED {symbol}: {num_contracts} contracts @ ${option_price:.2f} | Cost: ${cost:,.2f} | Conf: {confidence:.0f}%")
            
        except Exception as e:
            print(f"❌ Error entering options for {symbol}: {e}")
            # Fallback to stock trading
            self.enter_position(symbol, stock_price, confidence, 1.0)
    
    def check_option_positions(self):
        """Check and manage options positions"""
        if not self.options_enabled or not self.options_positions:
            return
        
        positions_to_close = self.options_trader.check_option_positions(self.options_positions)
        
        for option_symbol, exit_price, reason in positions_to_close:
            self.close_option_position(option_symbol, exit_price, reason)
    
    def close_option_position(self, option_symbol, exit_price, reason):
        """Close an options position"""
        if option_symbol not in self.options_positions:
            return
        
        try:
            position = self.options_positions[option_symbol]
            entry_price = position['entry_price']
            contracts = position['contracts']
            
            # Place sell order
            order = self.options_trader.place_option_order(option_symbol, contracts, side='sell')
            
            # Calculate P&L
            entry_cost = entry_price * contracts * 100
            exit_value = exit_price * contracts * 100
            pnl = exit_value - entry_cost
            pnl_pct = (exit_price - entry_price) / entry_price * 100
            
            # Record trade
            self.trades.append({
                'symbol': option_symbol,
                'underlying': position['underlying'],
                'type': 'option',
                'entry_price': entry_price,
                'exit_price': exit_price,
                'contracts': contracts,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'reason': reason,
                'entry_time': position['entry_time'],
                'exit_time': datetime.now().isoformat()
            })
            
            # Update cash
            self.cash += exit_value
            
            # Remove position
            del self.options_positions[option_symbol]
            self.save_state()
            
            emoji = "✅" if pnl > 0 else "❌"
            print(f"{emoji} OPTIONS CLOSED {position['underlying']}: {reason} | Entry: ${entry_price:.2f} | Exit: ${exit_price:.2f} | P&L: ${pnl:.2f} ({pnl_pct:+.1f}%)")
            
        except Exception as e:
            print(f"❌ Error closing option {option_symbol}: {e}")
