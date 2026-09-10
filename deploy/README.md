# Deploy Trading Bot to DigitalOcean

## Quick Start Guide

### 1. Create DigitalOcean Droplet
1. Go to https://www.digitalocean.com
2. Create account (get $200 free credit)
3. Click "Create" → "Droplets"
4. Choose:
   - **Ubuntu 22.04 LTS**
   - **Basic plan - $6/month**
   - **1GB RAM**
   - **New York datacenter**
5. Add SSH key or use password
6. Click "Create Droplet"
7. Note your droplet's IP address

### 2. Initial Server Setup
Connect to your server:
```bash
ssh root@YOUR_IP_ADDRESS
```

Run the setup script:
```bash
curl -o setup.sh https://raw.githubusercontent.com/YOUR_REPO/deploy/setup_server.sh
chmod +x setup.sh
./setup.sh
```

Or manually copy and run `deploy/setup_server.sh`

### 3. Deploy Your Bot

On your local machine:

1. Edit `deploy/deploy.sh` and replace `YOUR_SERVER_IP` with your droplet IP

2. Make it executable:
```bash
chmod +x deploy/deploy.sh
```

3. Run deployment:
```bash
./deploy/deploy.sh
```

### 4. Verify It's Running

SSH into your server:
```bash
ssh root@YOUR_IP_ADDRESS
```

Check bot status:
```bash
supervisorctl status
```

You should see:
```
crypto-bot    RUNNING   pid 1234, uptime 0:01:23
stock-bot     RUNNING   pid 1235, uptime 0:01:23
```

### 5. View Logs

Stock bot logs:
```bash
tail -f /var/log/stock-bot.out.log
```

Crypto bot logs:
```bash
tail -f /var/log/crypto-bot.out.log
```

### 6. Control Bots

Start/stop/restart:
```bash
supervisorctl start stock-bot
supervisorctl stop stock-bot
supervisorctl restart stock-bot
supervisorctl restart all
```

## Manual Deployment (Alternative)

If the script doesn't work, here's the manual process:

### 1. Connect to server
```bash
ssh root@YOUR_IP_ADDRESS
```

### 2. Install dependencies
```bash
apt-get update
apt-get install -y python3 python3-pip python3-venv supervisor
```

### 3. Create bot directory
```bash
mkdir -p /opt/trading-bot/bot
cd /opt/trading-bot
python3 -m venv venv
source venv/bin/activate
pip install requests python-dotenv alpaca-trade-api
```

### 4. Upload bot files
On your local machine:
```bash
cd backend
scp -r bot/ root@YOUR_IP:/opt/trading-bot/
scp .env root@YOUR_IP:/opt/trading-bot/
```

### 5. Configure supervisor
On server:
```bash
nano /etc/supervisor/conf.d/trading-bots.conf
```

Paste the contents from `deploy/supervisor_config.conf`

### 6. Start bots
```bash
supervisorctl reread
supervisorctl update
supervisorctl start all
```

## Troubleshooting

### Bot not starting
Check logs:
```bash
tail -100 /var/log/stock-bot.err.log
```

### Check if process is running
```bash
ps aux | grep python
```

### Restart everything
```bash
supervisorctl restart all
```

### Update bot code
```bash
cd /opt/trading-bot
# Upload new files
supervisorctl restart all
```

## Cost

- **Basic Droplet**: $6/month
- **With backups**: $7.20/month
- **Total**: ~$6-8/month

## Security Tips

1. **Set up firewall**:
```bash
ufw allow 22/tcp
ufw enable
```

2. **Create non-root user** (optional but recommended)

3. **Keep system updated**:
```bash
apt-get update && apt-get upgrade -y
```

## Monitoring

Check bot is running:
```bash
supervisorctl status
```

Check resource usage:
```bash
htop
```

Check disk space:
```bash
df -h
```

## Support

If you have issues:
1. Check logs: `/var/log/stock-bot.out.log`
2. Check supervisor status: `supervisorctl status`
3. Restart bots: `supervisorctl restart all`
