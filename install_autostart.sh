#!/bin/bash

echo "Installing Stock Trading Bot Auto-Start..."

# Copy the plist file to LaunchAgents
cp com.tradingbot.stockbot.plist ~/Library/LaunchAgents/

# Load the launch agent
launchctl load ~/Library/LaunchAgents/com.tradingbot.stockbot.plist

echo "✅ Auto-start installed!"
echo ""
echo "The bot will now start automatically when you log in."
echo ""
echo "To manage the bot:"
echo "  Stop:    launchctl stop com.tradingbot.stockbot"
echo "  Start:   launchctl start com.tradingbot.stockbot"
echo "  Disable: launchctl unload ~/Library/LaunchAgents/com.tradingbot.stockbot.plist"
echo ""
echo "Logs are saved to:"
echo "  backend/bot/launchd_stdout.log"
echo "  backend/bot/launchd_stderr.log"
