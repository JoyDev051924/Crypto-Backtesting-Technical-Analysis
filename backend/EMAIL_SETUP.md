# 📧 Email Notifications Setup

Get hourly updates on your bot's performance sent directly to your email!

## Quick Setup (5 minutes)

### Step 1: Get Gmail App Password

1. Go to your Google Account: https://myaccount.google.com/
2. Click "Security" in the left menu
3. Enable "2-Step Verification" (if not already enabled)
4. Go back to Security
5. Click "App passwords" (under 2-Step Verification)
6. Select "Mail" and "Other (Custom name)"
7. Name it "Trading Bot"
8. Click "Generate"
9. **Copy the 16-character password** (you'll need this)

### Step 2: Update .env File

Open `backend/.env` and update these lines:

```bash
# Replace with your actual email
NOTIFICATION_EMAIL=your_email@gmail.com

# Paste the 16-character app password from Step 1
NOTIFICATION_PASSWORD=abcd efgh ijkl mnop

# Email where you want to receive notifications
NOTIFICATION_TO=your_email@gmail.com
```

**Example:**
```bash
NOTIFICATION_EMAIL=john@gmail.com
NOTIFICATION_PASSWORD=xyzw abcd 1234 5678
NOTIFICATION_TO=john@gmail.com
```

### Step 3: Restart the Bot

```bash
# Stop current bot
pkill -f stock_bot

# Start with notifications enabled
cd backend
PYTHONPATH=$PWD venv/bin/python bot/stock_bot.py &
```

## What You'll Receive

**Every hour during market hours, you'll get an email with:**

📊 **Account Summary:**
- Total portfolio value
- Available cash
- Today's P&L (%)
- Total P&L ($)

📈 **Open Positions:**
- Symbol
- Quantity
- Entry price
- Current price
- P&L per position

**Example Email:**

```
🤖 Trading Bot Update - $103,450.00 (+3.45%)

Time: 2:00 PM EST

📊 Account Summary
• Total Value: $103,450.00
• Cash: $52,300.00
• Today's P&L: +3.45%
• Total P&L: +$3,450.00

📈 Open Positions (7)
┌─────────┬─────┬────────┬─────────┬────────┐
│ Symbol  │ Qty │ Entry  │ Current │ P&L    │
├─────────┼─────┼────────┼─────────┼────────┤
│ AAPL    │ 35  │ $185.50│ $189.20 │ +2.0%  │
│ MSFT    │ 17  │ $380.25│ $385.10 │ +1.3%  │
│ NVDA    │ 12  │ $495.00│ $510.50 │ +3.1%  │
└─────────┴─────┴────────┴─────────┴────────┘
```

## Troubleshooting

### Not Receiving Emails?

**Check 1: Verify .env settings**
```bash
cat backend/.env | grep NOTIFICATION
```
Make sure email and password are correct.

**Check 2: Check bot logs**
```bash
tail -f backend/bot/enhanced_bot.log
```
Look for "✅ Hourly update email sent" or error messages.

**Check 3: Gmail App Password**
- Make sure you used an App Password (not your regular password)
- App password should be 16 characters
- No spaces in the password in .env file

**Check 4: 2-Step Verification**
- Must be enabled on your Google account
- App passwords won't work without it

### Using a Different Email Provider?

**For Outlook/Hotmail:**
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

**For Yahoo:**
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

Update `bot/notifications.py` with the correct SMTP server.

## Customization

### Change Notification Frequency

Edit `bot/stock_bot.py`, line with `>= 3600`:

```python
# Every 30 minutes
if (current_time - self.last_notification_time).seconds >= 1800:

# Every 2 hours
if (current_time - self.last_notification_time).seconds >= 7200:
```

### Disable Notifications

Just comment out these lines in `.env`:
```bash
# NOTIFICATION_EMAIL=your_email@gmail.com
# NOTIFICATION_PASSWORD=your_app_password
# NOTIFICATION_TO=your_email@gmail.com
```

Or set to empty:
```bash
NOTIFICATION_TO=
```

## Privacy & Security

✅ **Your email password is stored locally** in `.env` (never committed to git)
✅ **Uses Gmail App Password** (not your actual password)
✅ **Can be revoked anytime** from Google Account settings
✅ **Only sends to your email** (no third parties)

---

**That's it!** You'll now get hourly updates on your bot's performance. 📧🤖
