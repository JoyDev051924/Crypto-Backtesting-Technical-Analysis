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

print("Testing Alpaca connection...")
print(f"API Key: {api_key[:10]}...")
print(f"Base URL: {base_url}")
print()

# Test account endpoint
response = requests.get(f'{base_url}/v2/account', headers=headers)
if response.status_code == 200:
    account = response.json()
    print("✓ Connection successful!")
    print(f"Account Status: {account.get('status')}")
    print(f"Cash: ${float(account.get('cash', 0)):,.2f}")
    print(f"Portfolio Value: ${float(account.get('portfolio_value', 0)):,.2f}")
    print(f"Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
else:
    print(f"✗ Connection failed: {response.status_code}")
    print(response.text)
