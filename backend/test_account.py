import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ALPACA_API_KEY')
api_secret = os.getenv('ALPACA_API_SECRET')
base_url = os.getenv('ALPACA_BASE_URL')

headers = {
    'APCA-API-KEY-ID': api_key,
    'APCA-API-SECRET-KEY': api_secret
}

print(f"Testing connection to: {base_url}")
print(f"API Key: {api_key[:10]}...")

try:
    response = requests.get(f'{base_url}/v2/account', headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        account = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"Account ID: {account.get('id')}")
        print(f"Cash: ${float(account.get('cash', 0)):,.2f}")
        print(f"Equity: ${float(account.get('equity', 0)):,.2f}")
        print(f"Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
        print(f"Account Type: {'LIVE' if 'paper' not in base_url else 'PAPER'}")
    else:
        print(f"\n❌ ERROR: {response.text}")
except Exception as e:
    print(f"\n❌ EXCEPTION: {e}")
