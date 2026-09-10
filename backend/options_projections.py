"""
OPTIONS TRADING PROJECTIONS
Based on leveraged returns with risk management
"""

starting = 3000

print("=" * 70)
print("OPTIONS TRADING - REALISTIC PROJECTIONS")
print("=" * 70)
print(f"\nStarting Capital: ${starting:,.2f}")
print("\n" + "=" * 70)

# Options typically give 5-10x leverage on stock movements
# If stock moves 1%, option moves 5-10%

print("\nSCENARIO 1: CONSERVATIVE OPTIONS STRATEGY")
print("-" * 70)
print("Strategy: 30% options, 70% stocks")
print("Options leverage: 5x")
print("Win rate: 60%")
print("")

# Conservative: 0.3% avg daily on stocks = 1.5% on options
stock_portion = starting * 0.7
options_portion = starting * 0.3

# Simulate 1 year (252 trading days)
days = 252
stock_daily = 0.003  # 0.3% per day on stocks
options_daily = stock_daily * 5  # 5x leverage = 1.5% per day

stock_value = stock_portion * ((1 + stock_daily) ** days)
options_value = options_portion * ((1 + options_daily * 0.6) ** days)  # 60% win rate
total = stock_value + options_value

print(f"After 1 year:")
print(f"  Stock portion:   ${stock_value:>12,.2f}")
print(f"  Options portion: ${options_value:>12,.2f}")
print(f"  Total:           ${total:>12,.2f}")
print(f"  Profit:          ${total - starting:>12,.2f}")
print(f"  Return:          {((total/starting - 1) * 100):>11.1f}%")

print("\n" + "=" * 70)
print("\nSCENARIO 2: MODERATE OPTIONS STRATEGY")
print("-" * 70)
print("Strategy: 50% options, 50% stocks")
print("Options leverage: 7x")
print("Win rate: 65%")
print("")

stock_portion = starting * 0.5
options_portion = starting * 0.5

stock_daily = 0.004  # 0.4% per day on stocks
options_daily = stock_daily * 7  # 7x leverage = 2.8% per day

stock_value = stock_portion * ((1 + stock_daily) ** days)
options_value = options_portion * ((1 + options_daily * 0.65) ** days)  # 65% win rate
total = stock_value + options_value

print(f"After 1 year:")
print(f"  Stock portion:   ${stock_value:>12,.2f}")
print(f"  Options portion: ${options_value:>12,.2f}")
print(f"  Total:           ${total:>12,.2f}")
print(f"  Profit:          ${total - starting:>12,.2f}")
print(f"  Return:          {((total/starting - 1) * 100):>11.1f}%")

print("\n" + "=" * 70)
print("\nSCENARIO 3: AGGRESSIVE OPTIONS STRATEGY")
print("-" * 70)
print("Strategy: 70% options, 30% stocks")
print("Options leverage: 10x")
print("Win rate: 70%")
print("")

stock_portion = starting * 0.3
options_portion = starting * 0.7

stock_daily = 0.005  # 0.5% per day on stocks
options_daily = stock_daily * 10  # 10x leverage = 5% per day

stock_value = stock_portion * ((1 + stock_daily) ** days)
options_value = options_portion * ((1 + options_daily * 0.7) ** days)  # 70% win rate
total = stock_value + options_value

print(f"After 1 year:")
print(f"  Stock portion:   ${stock_value:>12,.2f}")
print(f"  Options portion: ${options_value:>12,.2f}")
print(f"  Total:           ${total:>12,.2f}")
print(f"  Profit:          ${total - starting:>12,.2f}")
print(f"  Return:          {((total/starting - 1) * 100):>11.1f}%")

print("\n" + "=" * 70)
print("\nMONTHLY PROGRESSION (Moderate Strategy)")
print("-" * 70)

stock_portion = starting * 0.5
options_portion = starting * 0.5
stock_daily = 0.004
options_daily = stock_daily * 7

print(f"{'Month':<10} {'Total Value':<20} {'Monthly Gain':<20}")
print("-" * 70)

prev_total = starting
for month in range(1, 13):
    days_in_month = 21
    stock_val = stock_portion * ((1 + stock_daily) ** (days_in_month * month))
    options_val = options_portion * ((1 + options_daily * 0.65) ** (days_in_month * month))
    total_val = stock_val + options_val
    monthly_gain = total_val - prev_total
    
    print(f"Month {month:<3}  ${total_val:>18,.2f} ${monthly_gain:>18,.2f}")
    prev_total = total_val

print("-" * 70)

print("\n" + "=" * 70)
print("\n🎯 BEST CASE SCENARIOS (Everything goes right)")
print("-" * 70)

scenarios = [
    ("Conservative (30% options)", 0.3, 5, 0.6, 0.003),
    ("Moderate (50% options)", 0.5, 7, 0.65, 0.004),
    ("Aggressive (70% options)", 0.7, 10, 0.7, 0.005),
    ("All-in (100% options)", 1.0, 10, 0.75, 0.006),
]

for name, opt_pct, leverage, win_rate, daily in scenarios:
    stock_portion = starting * (1 - opt_pct)
    options_portion = starting * opt_pct
    
    stock_value = stock_portion * ((1 + daily) ** days) if stock_portion > 0 else 0
    options_value = options_portion * ((1 + daily * leverage * win_rate) ** days)
    total = stock_value + options_value
    
    print(f"\n{name}")
    print(f"  ${starting:,.0f} → ${total:,.2f} (+${total-starting:,.2f})")

print("\n" + "=" * 70)
print("\n⚠️  REALITY CHECK")
print("-" * 70)
print("✅ WHAT COULD HAPPEN:")
print("   • Best case: $3,000 → $20,000-50,000 in a year")
print("   • Realistic: $3,000 → $8,000-15,000 in a year")
print("   • Bad case: $3,000 → $1,000-2,000 (big loss)")
print("")
print("❌ RISKS:")
print("   • Options expire worthless if wrong")
print("   • One bad week could lose 30-50%")
print("   • Need 60%+ win rate to profit")
print("   • Time decay eats profits")
print("   • More complex to manage")
print("")
print("💡 MY WINNING PLAN:")
print("   1. Prove stock bot works (2-4 weeks)")
print("   2. Start with 20% in options")
print("   3. Only trade highest confidence (85%+)")
print("   4. Use weekly options (less time decay)")
print("   5. Scale up if profitable")
print("")
print("🎯 REALISTIC TARGET:")
print("   $3,000 → $10,000-15,000 in first year")
print("   That's 233-400% return - life changing!")
print("\n" + "=" * 70)
