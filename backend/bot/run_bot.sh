#!/bin/bash
# Run the paper trading bot

cd "$(dirname "$0")/.."
source venv/bin/activate
python -m bot.trading_bot
