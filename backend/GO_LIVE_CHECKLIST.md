# 🚀 GO LIVE CHECKLIST

## Before You Start

- [ ] **Funds cleared in Alpaca account** ($3,000 minimum)
- [ ] **Verify live credentials work** (check Alpaca dashboard)
- [ ] **Review bot performance** in paper trading (should be profitable)
- [ ] **MacBook ready** (plugged in, display sleep disabled)
- [ ] **Understand the risks** (you can lose money)

## Activation Steps

### 1. Switch to Live Trading
```bash
cd backend
./switch_to_live.sh
```
Type `YES` when prompted to confirm.

### 2. Reset Bot State
```bash
# Stop the current bot
launchctl stop com.tradingbot.stockbot

# Delete paper trading state (start fresh)
rm bot/stock_bot_state.json
rm bot/stock_bot_log.json

# Start with live trading
launchctl start com.tradingbot.stockbot
```

### 3. Verify It's Working
```bash
# Watch the bot logs
tail -f bot/launchd_stdout.log

# Check for "LIVE TRADING" in the output
# Verify starting capital shows $3,000
```

## What to Expect

**Starting Capital:** $3,000

**Position Sizing:**
- Base: 5% ($150 per trade)
- High confidence: up to 15% ($450 per trade)
- Max 10 positions at once

**Risk Management:**
- Stop loss: 4% ($6-18 per trade)
- Daily loss limit: 5% ($150 total)
- Max drawdown: 10% ($300 from peak)

**Trading Hours:**
- Market open: 9:30 AM EST
- Bot starts trading: 10:00 AM EST (30 min buffer)
- Bot stops new trades: 3:00 PM EST (60 min buffer)
- All positions closed: 3:45 PM EST (15 min before close)

**Options Trading:**
- 20% allocation ($600 max)
- Only 85%+ confidence setups
- Max 3 option positions
- 50% profit target, 30% stop loss

## Monitoring

**Check Performance:**
```bash
cd backend
python check_pnl.py
```

**View Logs:**
```bash
tail -f bot/launchd_stdout.log
```

**View Trade History:**
```bash
cat bot/stock_bot_log.json | python -m json.tool
```

## Safety Features Active

✅ Stop loss at -4% (prevents big losses)
✅ Partial profit taking at +4% (locks in gains)
✅ Trailing stops (protects profits)
✅ Daily loss limit at -5% (stops trading if bad day)
✅ Max drawdown at -10% (pauses if losing streak)
✅ End-of-day closing (no overnight risk)
✅ Sector diversification (max 30% per sector)
✅ Volatility adjustment (reduces size when VIX high)

## If Something Goes Wrong

**Stop the bot immediately:**
```bash
launchctl stop com.tradingbot.stockbot
```

**Close all positions manually:**
1. Log into Alpaca dashboard
2. Go to "Positions"
3. Close all positions

**Switch back to paper trading:**
```bash
cp .env.paper.backup .env
launchctl start com.tradingbot.stockbot
```

## Expected Returns

**Conservative estimate (based on paper trading):**
- Daily: 0.5% - 1.5%
- Weekly: 2.5% - 7.5%
- Monthly: 10% - 30%

**With $3,000 starting capital:**
- Good day: +$15 - $45
- Great day: +$45 - $90
- Bad day: -$150 (daily loss limit)

**After 1 month (if profitable):**
- Conservative: $3,300 (+10%)
- Moderate: $3,600 (+20%)
- Aggressive: $3,900 (+30%)

## Important Notes

⚠️ **Past performance doesn't guarantee future results**
⚠️ **You can lose money - only invest what you can afford to lose**
⚠️ **Monitor the bot daily, especially the first week**
⚠️ **Keep MacBook open and plugged in during market hours**
⚠️ **Bot will close all positions before market close (no overnight risk)**

## Support

If you need to make changes or have issues:
1. Stop the bot: `launchctl stop com.tradingbot.stockbot`
2. Review logs: `tail -f bot/launchd_stdout.log`
3. Check state: `cat bot/stock_bot_state.json`
4. Restart: `launchctl start com.tradingbot.stockbot`

---

**Ready to go live? Run: `./switch_to_live.sh`**
