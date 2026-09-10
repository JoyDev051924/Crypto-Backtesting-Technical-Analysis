import math

# Today's performance
starting_capital = 100000
current_value = 100877.11
daily_return = 0.0088  # 0.88%

print("=" * 70)
print("TRADING BOT - MONTHLY PROJECTIONS")
print("=" * 70)
print(f"\n📊 Today's Performance:")
print(f"   Starting: ${starting_capital:,.2f}")
print(f"   Current:  ${current_value:,.2f}")
print(f"   Gain:     ${current_value - starting_capital:+,.2f} ({daily_return*100:+.2f}%)")
print("\n" + "=" * 70)

# Calculate different scenarios
scenarios = [
    ("Conservative (0.5% avg/day)", 0.005),
    ("Today's Performance (0.88%/day)", daily_return),
    ("Optimistic (1.5% avg/day)", 0.015),
    ("Aggressive (2% avg/day)", 0.02),
]

trading_days_per_month = 21  # ~21 trading days per month

print("\nMONTHLY PROJECTIONS (Compounding Daily):")
print("-" * 70)
print(f"{'Scenario':<35} {'1 Month':<15} {'Gain':<15}")
print("-" * 70)

for scenario_name, avg_daily_return in scenarios:
    # Compound daily returns
    month_value = starting_capital * ((1 + avg_daily_return) ** trading_days_per_month)
    month_gain = month_value - starting_capital
    month_return_pct = (month_gain / starting_capital) * 100
    
    print(f"{scenario_name:<35} ${month_value:>13,.2f} ${month_gain:>13,.2f} ({month_return_pct:+.1f}%)")

print("-" * 70)

# Extended projections at today's rate
print(f"\n\nIF WE MAINTAIN TODAY'S RATE (0.88%/day):")
print("-" * 70)
print(f"{'Period':<20} {'Portfolio Value':<20} {'Total Gain':<20}")
print("-" * 70)

periods = [
    ("1 Week (5 days)", 5),
    ("2 Weeks (10 days)", 10),
    ("1 Month (21 days)", 21),
    ("2 Months (42 days)", 42),
    ("3 Months (63 days)", 63),
]

for period_name, days in periods:
    value = starting_capital * ((1 + daily_return) ** days)
    gain = value - starting_capital
    return_pct = (gain / starting_capital) * 100
    print(f"{period_name:<20} ${value:>18,.2f} ${gain:>18,.2f} ({return_pct:+.1f}%)")

print("-" * 70)

# Reality check
print("\n\n⚠️  REALITY CHECK:")
print("-" * 70)
print("1. Today was ONE day - not a pattern yet")
print("2. Markets have good days and bad days")
print("3. Realistic expectation: 5-15% per MONTH (not per day)")
print("4. Professional traders average 10-20% per YEAR")
print("5. The bot needs weeks of data to prove consistency")
print("\n📈 REALISTIC MONTHLY TARGETS:")
print("   Conservative: $105,000 (+5%)")
print("   Moderate:     $110,000 (+10%)")
print("   Optimistic:   $115,000 (+15%)")
print("\n💡 RECOMMENDATION:")
print("   Let it run for 2-4 weeks in paper trading")
print("   Track win rate, average return, max drawdown")
print("   Then decide if it's worth real money")
print("\n" + "=" * 70)
