"""
Email Notification Module
Sends hourly updates on positions and P&L
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

class EmailNotifier:
    def __init__(self, email_to):
        self.email_to = email_to
        # Using Gmail SMTP (you can change this)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        # Will use app password from .env
        self.email_from = os.getenv('NOTIFICATION_EMAIL')
        self.email_password = os.getenv('NOTIFICATION_PASSWORD')
        
    def send_hourly_update(self, positions, cash, total_value, daily_pnl, total_pnl):
        """Send hourly position and P&L update"""
        try:
            subject = f"🤖 Trading Bot Update - ${total_value:,.2f} ({daily_pnl:+.2f}%)"
            
            # Build email body
            body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2>Trading Bot Hourly Update</h2>
    <p><strong>Time:</strong> {datetime.now().strftime('%I:%M %p EST')}</p>
    
    <h3>📊 Account Summary</h3>
    <ul>
        <li><strong>Total Value:</strong> ${total_value:,.2f}</li>
        <li><strong>Cash:</strong> ${cash:,.2f}</li>
        <li><strong>Today's P&L:</strong> <span style="color: {'green' if daily_pnl >= 0 else 'red'};">{daily_pnl:+.2f}%</span></li>
        <li><strong>Total P&L:</strong> <span style="color: {'green' if total_pnl >= 0 else 'red'};">${total_pnl:+,.2f}</span></li>
    </ul>
"""
            
            if positions:
                body += f"""
    <h3>📈 Open Positions ({len(positions)})</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f2f2f2;">
            <th style="border: 1px solid #ddd; padding: 8px;">Symbol</th>
            <th style="border: 1px solid #ddd; padding: 8px;">Qty</th>
            <th style="border: 1px solid #ddd; padding: 8px;">Entry</th>
            <th style="border: 1px solid #ddd; padding: 8px;">Current</th>
            <th style="border: 1px solid #ddd; padding: 8px;">P&L</th>
        </tr>
"""
                for symbol, pos in positions.items():
                    current_price = pos.get('current_price', pos['entry_price'])
                    pnl_pct = ((current_price - pos['entry_price']) / pos['entry_price']) * 100
                    color = 'green' if pnl_pct >= 0 else 'red'
                    
                    body += f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>{symbol}</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{pos['quantity']}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">${pos['entry_price']:.2f}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">${current_price:.2f}</td>
            <td style="border: 1px solid #ddd; padding: 8px; color: {color};">{pnl_pct:+.2f}%</td>
        </tr>
"""
                body += "    </table>"
            else:
                body += "    <p><em>No open positions</em></p>"
            
            body += """
    <hr>
    <p style="color: #666; font-size: 12px;">This is an automated message from your trading bot.</p>
</body>
</html>
"""
            
            # Send email
            self._send_email(subject, body)
            print(f"✅ Hourly update email sent to {self.email_to}")
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
    
    def _send_email(self, subject, body):
        """Send email via SMTP"""
        msg = MIMEMultipart('alternative')
        msg['From'] = self.email_from
        msg['To'] = self.email_to
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.send_message(msg)
