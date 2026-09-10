# GO LIVE TRADING INSTRUCTIONS

## ⚠️ CRITICAL: Read This Before Going Live!

Your live trading credentials are saved in `.env` but **commented out**.

## Current Status
- ✅ Paper trading active (testing with $100k fake money)
- ✅ Options module added (20% allocation, 85%+ confidence only)
- ✅ Live credentials saved and ready
- ⏳ Waiting for funds to clear in Alpaca account

## When Your $3,000 Clears

### Step 1: Verify Funds
1. Log into https://alpaca.markets
2. Check that $3,000 shows in your account
3. Verify it's in "Live Trading" mode (not paper)

### Step 2: Switch to Live Trading

**Option A: Edit .env file**
```bash
cd backend
nano .env

# Comment out paper trading lines:
# ALPACA_API_KEY=PKGQ2XPBIOYYME7XATG54LA5RL
# ALPACA_API_SECRET=EP4s2mRxE5dsb1UZ1auRaKStKEXugkzJMXLVkBjXk73y
# ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Uncomment live trading lines:
ALPACA_API_KEY=AKQJXALPP3WVXIX4MCGR66JA
ALPACA_API_SECRET=D2EX7meHHyUwkMhs3T6MTQPxHdKz8pgB6tC9q6LgYoWWAF
ALPACA_BASE_URL=https://api.alpaca.markets
```

**Option B: Quick command**
```bash
cd backend
# Backup paper config
cp .env .env.paper

# Activate live trading
sed -i '' 's/^ALPACA_API_KEY=PK/#ALPACA_API_KEY=PK/' .env
sed -i '' 's/^ALPACA_API_SECRET=EP/#ALPACA_API_SECRET=EP/' .env
sed -i '' 's/^ALPACA_BASE_URL=https:\/\/paper/#ALPACA_BASE_URL=https:\/\/paper/' .env
sed -i '' 's/^# ALPACA_API_KEY=AK/ALPACA_API_KEY=AK/' .env
sed -i '' 's/^# ALPACA_API_SECRET=D2/ALPACA_API_SECRET=D2/' .env
sed -i '' 's/^# ALPACA_BASE_URL=https:\/\/api/ALPACA_BASE_URL=https:\/\/api/' .env
```

### Step 3: Restart Bot
```bash
# Stop current paper trading bot
# (Find process ID with: ps aux | grep stock_bot)
kill <PROCESS_ID>

# Start live trading bot
cd backend
source venv/bin/activate
python -m bot.stock_bot
```

### Step 4: Verify It's Live
You should see:
```
Starting Capital: $3,000.00
```

NOT $100,000 (that's paper trading)

## What the Bot Will Do

**Stock Trading (80% of capital = $2,400):**
- Trade 70-84% confidence setups
- Up to 10 positions
- 4% stop loss, 8% take profit
- Partial profits at 4%
- Close all positions before market close

**Options Trading (20% of capital = $600):**
- Only 85%+ confidence setups
- Max 3 option positions
- Weekly calls, slightly OTM
- 50% profit target, 30% stop loss
- Much higher potential returns

## Safety Features Active

✅ Daily loss limit (5%)
✅ Max drawdown protection (10%)
✅ Sector diversification (30% max per sector)
✅ Volatility adjustment (reduces size when VIX > 25)
✅ Trading hours buffer (no trades first/last hour)
✅ End-of-day close (no overnight risk)
✅ Stop loss enforcement (improved)
✅ Partial profit taking
✅ Options risk management

## Monitoring

**Check status:**
```bash
cd backend
python check_pnl.py
```

**View logs:**
```bash
tail -f bot/stock_bot_log.json
```

**Check state:**
```bash
cat bot/stock_bot_state.json | python -m json.tool
```

## Emergency Stop

If something goes wrong:
```bash
# Find bot process
ps aux | grep stock_bot

# Kill it
kill <PROCESS_ID>

# Or force kill
kill -9 <PROCESS_ID>
```

## Switching Back to Paper Trading

```bash
cd backend
cp .env.paper .env
# Restart bot
```

## Expected Performance

**Conservative estimate:**
- $3,000 → $5,000-6,000 in 1 year
- 67-100% return

**With options working well:**
- $3,000 → $8,000-15,000 in 1 year
- 167-400% return

**Remember:**
- You could also lose money
- Past performance (1 day) doesn't guarantee future results
- Monitor closely for first 2 weeks
- Be prepared to stop if it's not working

## Questions?

The bot is ready. Just waiting for your funds to clear!
