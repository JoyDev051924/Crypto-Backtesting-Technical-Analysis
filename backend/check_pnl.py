import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ALPACA_API_KEY')
api_secret = os.getenv('ALPACA_API_SECRET')
base_url = os.getenv('ALPACA_BASE_URL')

headers = {
    'APCA-API-KEY-ID': api_key,
    'APCA-API-SECRET-KEY': api_secret
}

# Load current positions
with open('bot/stock_bot_state.json', 'r') as f:
    state = json.load(f)

cash = state['cash']
positions = state['positions']

print("=" * 70)
print("STOCK BOT - LIVE P&L")
print("=" * 70)
print(f"\n💰 Cash: ${cash:,.2f}")
print(f"📊 Open Positions: {len(positions)}")
print("\n" + "-" * 70)
print(f"{'Symbol':<8} {'Entry':<10} {'Current':<10} {'Qty':<6} {'P&L $':<12} {'P&L %':<8}")
print("-" * 70)

total_pnl = 0
total_current_value = 0

for symbol, pos in positions.items():
    entry_price = pos['entry_price']
    quantity = pos['quantity']
    
    # Get current price from Alpaca
    try:
        url = f'https://data.alpaca.markets/v2/stocks/{symbol}/bars'
        params = {
            'timeframe': '1Min',
            'limit': 1
        }
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        if 'bars' in data and len(data['bars']) > 0:
            current_price = float(data['bars'][-1]['c'])
        else:
            current_price = entry_price  # Fallback
    except:
        current_price = entry_price  # Fallback on error
    
    # Calculate P&L
    entry_value = entry_price * quantity
    current_value = current_price * quantity
    pnl = current_value - entry_value
    pnl_pct = (pnl / entry_value) * 100
    
    total_pnl += pnl
    total_current_value += current_value
    
    # Color code P&L
    pnl_str = f"${pnl:+,.2f}"
    pnl_pct_str = f"{pnl_pct:+.2f}%"
    
    print(f"{symbol:<8} ${entry_price:<9.2f} ${current_price:<9.2f} {quantity:<6} {pnl_str:<12} {pnl_pct_str:<8}")

print("-" * 70)

portfolio_value = cash + total_current_value
total_return_pct = ((portfolio_value - 100000) / 100000) * 100

print(f"\n📈 Total Position Value: ${total_current_value:,.2f}")
print(f"💼 Total Portfolio Value: ${portfolio_value:,.2f}")
print(f"💵 Total P&L: ${total_pnl:+,.2f}")
print(f"📊 Total Return: {total_return_pct:+.2f}%")

if total_return_pct > 0:
    print(f"\n✅ UP ${total_pnl:,.2f} today!")
elif total_return_pct < 0:
    print(f"\n❌ DOWN ${total_pnl:,.2f} today")
else:
    print(f"\n➡️  FLAT (no change)")

print("\n" + "=" * 70)
