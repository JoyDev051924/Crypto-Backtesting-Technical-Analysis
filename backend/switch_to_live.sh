#!/bin/bash

echo "=========================================="
echo "SWITCHING TO LIVE TRADING"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will trade with REAL MONEY!"
echo ""
read -p "Are you sure you want to activate live trading? (type 'YES' to confirm): " confirm

if [ "$confirm" != "YES" ]; then
    echo "❌ Cancelled. Staying in paper trading mode."
    exit 1
fi

echo ""
echo "Backing up current .env..."
cp .env .env.paper.backup

echo "Switching to live trading credentials..."

# Update .env file
cat > .env << 'EOF'
# Copy this to .env and fill in your keys
# NEVER commit .env to git!

KRAKEN_API_KEY=3WsgdwA7bXY/Iee+fi63ojkZ3HUcVRF1axV1SPplAU6lWEYRB6KJWh8J
KRAKEN_API_SECRET=O+jJGHFImQhg5oQHUCi2Rapw2pAVCzgi8D7dhcWF1yEOe8orzvuTxv6T6bjRc0qIZDDdN6n0hIkLeL/BwZ4wqQ==

# Alpaca API (Stock Trading) - LIVE TRADING ACTIVE
ALPACA_API_KEY=AKQJXALPP3WVXIX4MCGR66JA
ALPACA_API_SECRET=D2EX7meHHyUwkMhs3T6MTQPxHdKz8pgB6tC9q6LgYoWWAF
ALPACA_BASE_URL=https://api.alpaca.markets

# PAPER TRADING CREDENTIALS (Backed up)
# ALPACA_API_KEY=PKGQ2XPBIOYYME7XATG54LA5RL
# ALPACA_API_SECRET=EP4s2mRxE5dsb1UZ1auRaKStKEXugkzJMXLVkBjXk73y
# ALPACA_BASE_URL=https://paper-api.alpaca.markets
EOF

echo ""
echo "✅ LIVE TRADING ACTIVATED!"
echo ""
echo "Next steps:"
echo "1. Stop the current bot: launchctl stop com.tradingbot.stockbot"
echo "2. Delete paper trading state: rm bot/stock_bot_state.json"
echo "3. Start fresh with live trading: launchctl start com.tradingbot.stockbot"
echo ""
echo "Or just restart your computer and it will auto-start with live trading."
echo ""
echo "📊 Your paper trading backup is saved at: .env.paper.backup"
echo ""
echo "⚠️  REMEMBER: You're now trading with REAL MONEY!"
echo "   - Starting capital: $3,000"
echo "   - Max positions: 10"
echo "   - Position sizes: 5-15% per trade"
echo "   - Stop loss: 4%"
echo "   - Daily loss limit: 5% ($150)"
echo "   - All positions close before market close"
echo ""
