#!/bin/bash
# Deploy bot to DigitalOcean server

# Configuration
SERVER_IP="YOUR_SERVER_IP"  # Replace with your droplet IP
SERVER_USER="root"

echo "=========================================="
echo "Deploying Trading Bot to DigitalOcean"
echo "=========================================="

# Create deployment package
echo "Creating deployment package..."
cd backend
tar -czf ../bot-deploy.tar.gz bot/ .env

cd ..

# Upload to server
echo "Uploading files to server..."
scp bot-deploy.tar.gz $SERVER_USER@$SERVER_IP:/tmp/

# Extract and setup on server
echo "Setting up on server..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /opt/trading-bot
tar -xzf /tmp/bot-deploy.tar.gz
rm /tmp/bot-deploy.tar.gz

# Copy supervisor config
cp /opt/trading-bot/deploy/supervisor_config.conf /etc/supervisor/conf.d/trading-bots.conf

# Reload supervisor
supervisorctl reread
supervisorctl update
supervisorctl restart all

echo "Deployment complete!"
echo "Check bot status with: supervisorctl status"
ENDSSH

# Cleanup
rm bot-deploy.tar.gz

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "To check bot status:"
echo "  ssh $SERVER_USER@$SERVER_IP"
echo "  supervisorctl status"
echo ""
echo "To view logs:"
echo "  tail -f /var/log/stock-bot.out.log"
echo "  tail -f /var/log/crypto-bot.out.log"
echo ""
