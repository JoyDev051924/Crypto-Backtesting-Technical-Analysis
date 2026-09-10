import math

starting_capital = 1000
trading_days_per_year = 252  # ~252 trading days in a year

print("=" * 70)
print("$1,000 INVESTMENT - 1 YEAR PROJECTIONS")
print("=" * 70)

scenarios = [
    ("Conservative (0.2% avg/day)", 0.002, "Realistic for algo trading"),
    ("Moderate (0.4% avg/day)", 0.004, "Good performance"),
    ("Today's Rate (0.88%/day)", 0.0088, "Unsustainable long-term"),
    ("Aggressive (1% avg/day)", 0.01, "Extremely rare"),
]

print(f"\nStarting Capital: ${starting_capital:,.2f}")
print("\n" + "-" * 70)
print(f"{'Scenario':<30} {'1 Year Value':<15} {'Profit':<15} {'Note'}")
print("-" * 70)

for scenario_name, daily_return, note in scenarios:
    year_value = starting_capital * ((1 + daily_return) ** trading_days_per_year)
    profit = year_value - starting_capital
    
    print(f"{scenario_name:<30} ${year_value:>13,.2f} ${profit:>13,.2f} {note}")

print("-" * 70)

# Monthly breakdown at different rates
print("\n\nMONTHLY PROGRESSION (Conservative 0.2%/day):")
print("-" * 70)
print(f"{'Month':<10} {'Portfolio Value':<20} {'Monthly Gain':<20}")
print("-" * 70)

daily_return = 0.002
prev_value = starting_capital

for month in range(1, 13):
    days = 21  # ~21 trading days per month
    current_value = prev_value * ((1 + daily_return) ** days)
    monthly_gain = current_value - prev_value
    
    print(f"Month {month:<3}  ${current_value:>18,.2f} ${monthly_gain:>18,.2f}")
    prev_value = current_value

print("-" * 70)

# Comparison with traditional investments
print("\n\nCOMPARISON WITH TRADITIONAL INVESTMENTS:")
print("-" * 70)
print(f"{'Investment Type':<30} {'1 Year Value':<20} {'Return'}")
print("-" * 70)

traditional = [
    ("Savings Account (0.5% APY)", 1000 * 1.005, "0.5%"),
    ("CD / Bonds (4% APY)", 1000 * 1.04, "4%"),
    ("S&P 500 Average (10% APY)", 1000 * 1.10, "10%"),
    ("Good Day Trader (20% APY)", 1000 * 1.20, "20%"),
    ("Bot Conservative (0.2%/day)", 1000 * ((1.002) ** 252), "64%"),
    ("Bot Moderate (0.4%/day)", 1000 * ((1.004) ** 252), "175%"),
]

for name, value, return_pct in traditional:
    print(f"{name:<30} ${value:>18,.2f} {return_pct:>10}")

print("-" * 70)

# Reality check
print("\n\n⚠️  REALITY CHECK:")
print("-" * 70)
print("✅ REALISTIC EXPECTATIONS:")
print("   - Conservative (0.2%/day): $1,000 → $1,640 (+$640)")
print("   - This beats most investments")
print("   - Still excellent if achieved")
print("")
print("❌ UNREALISTIC EXPECTATIONS:")
print("   - Maintaining 0.88%/day for a year")
print("   - Would turn $1k into $10k+")
print("   - No trader does this consistently")
print("")
print("💡 WHAT'S LIKELY TO HAPPEN:")
print("   - Some months up 10-20%")
print("   - Some months down 5-10%")
print("   - Overall: 30-80% gain for the year")
print("   - $1,000 → $1,300-1,800 is realistic")
print("")
print("🎯 BEST CASE SCENARIO:")
print("   If bot averages 0.3%/day:")
print("   $1,000 → $2,200 (+$1,200 profit)")
print("   That's 120% annual return - incredible!")
print("\n" + "=" * 70)
