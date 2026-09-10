#!/bin/bash
# Check bot status on Lightsail server

SERVER_IP="3.144.243.87"
KEY_FILE="backend/test1.pem"

echo "=========================================="
echo "Trading Bot Status Check"
echo "=========================================="
echo ""

echo "Bot Processes:"
ssh -i $KEY_FILE ubuntu@$SERVER_IP 'sudo supervisorctl status'
echo ""

echo "Stock Bot State:"
ssh -i $KEY_FILE ubuntu@$SERVER_IP 'cat /opt/trading-bot/bot/stock_bot_state.json 2>/dev/null || echo "No state file yet"'
echo ""

echo "Crypto Bot State:"
ssh -i $KEY_FILE ubuntu@$SERVER_IP 'cat /opt/trading-bot/bot/bot_v3_state.json 2>/dev/null || echo "No state file yet"'
echo ""

echo "Recent Stock Bot Logs (last 10 lines):"
ssh -i $KEY_FILE ubuntu@$SERVER_IP 'sudo tail -10 /var/log/stock-bot.out.log 2>/dev/null || echo "No logs yet"'
echo ""

echo "=========================================="
echo "To view live logs:"
echo "  ssh -i $KEY_FILE ubuntu@$SERVER_IP"
echo "  sudo tail -f /var/log/stock-bot.out.log"
echo "=========================================="
