"""
SWITCH TO LIVE TRADING

⚠️  WARNING: This will trade with REAL MONEY!
⚠️  Only run this if you understand the risks!

Before running:
1. Create Alpaca live trading account
2. Fund it with money you can afford to lose
3. Get your LIVE API keys (different from paper!)
4. Update .env file with live keys
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("⚠️  LIVE TRADING ACTIVATION CHECK")
print("=" * 70)

# Check if user has live keys
api_key = os.getenv('ALPACA_API_KEY')
base_url = os.getenv('ALPACA_BASE_URL')

print(f"\nCurrent API Key: {api_key[:10]}...")
print(f"Current Base URL: {base_url}")

if 'paper' in base_url:
    print("\n❌ You're still using PAPER TRADING keys!")
    print("\nTo switch to live trading:")
    print("1. Get your LIVE API keys from Alpaca")
    print("2. Update backend/.env:")
    print("   ALPACA_API_KEY=YOUR_LIVE_KEY")
    print("   ALPACA_API_SECRET=YOUR_LIVE_SECRET")
    print("   ALPACA_BASE_URL=https://api.alpaca.markets")
    print("\n3. Restart the bot")
else:
    print("\n✅ You're using LIVE TRADING keys!")
    print("\n⚠️  FINAL WARNING:")
    print("   - This will trade with REAL MONEY")
    print("   - You can LOSE money")
    print("   - Start with a small amount ($500-1000)")
    print("   - Monitor it closely for the first week")
    
    response = input("\nType 'I UNDERSTAND THE RISKS' to continue: ")
    if response == "I UNDERSTAND THE RISKS":
        print("\n✅ Live trading enabled. Restart the bot to begin.")
    else:
        print("\n❌ Cancelled. Good choice - wait for more data!")

print("\n" + "=" * 70)
