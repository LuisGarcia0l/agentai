#!/usr/bin/env python3
"""
Binance Testnet Integration for AI Trading System v2.0
Simple, lightweight integration for Mac M2
"""

import os
import json
import hmac
import hashlib
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional

class BinanceTestnet:
    """Simple Binance Testnet client"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key or os.getenv('BINANCE_API_KEY', '')
        self.secret_key = secret_key or os.getenv('BINANCE_SECRET_KEY', '')
        self.base_url = "https://testnet.binance.vision/api/v3"
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({'X-MBX-APIKEY': self.api_key})
    
    def _generate_signature(self, params: str) -> str:
        """Generate signature for authenticated requests"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make request to Binance API"""
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            params['signature'] = self._generate_signature(query_string)
        
        try:
            response = self.session.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def get_server_time(self) -> Dict:
        """Get server time"""
        return self._make_request("/time")
    
    def get_exchange_info(self) -> Dict:
        """Get exchange information"""
        return self._make_request("/exchangeInfo")
    
    def get_ticker_price(self, symbol: str = None) -> Dict:
        """Get ticker price"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request("/ticker/price", params)
    
    def get_24hr_ticker(self, symbol: str = None) -> Dict:
        """Get 24hr ticker statistics"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request("/ticker/24hr", params)
    
    def get_account_info(self) -> Dict:
        """Get account information (requires API keys)"""
        if not self.api_key or not self.secret_key:
            return {"error": "API keys required"}
        return self._make_request("/account", signed=True)
    
    def get_balances(self) -> List[Dict]:
        """Get account balances"""
        account_info = self.get_account_info()
        if "error" in account_info:
            return []
        return account_info.get("balances", [])
    
    def test_connectivity(self) -> bool:
        """Test API connectivity"""
        try:
            result = self.get_server_time()
            return "serverTime" in result
        except:
            return False

def test_binance_testnet():
    """Test Binance testnet connectivity"""
    print("🧪 Testing Binance Testnet Connection...")
    print("-" * 40)
    
    client = BinanceTestnet()
    
    # Test connectivity
    if client.test_connectivity():
        print("✅ Binance Testnet - Connected")
    else:
        print("❌ Binance Testnet - Connection failed")
        return False
    
    # Get server time
    server_time = client.get_server_time()
    if "serverTime" in server_time:
        dt = datetime.fromtimestamp(server_time["serverTime"] / 1000)
        print(f"✅ Server Time: {dt}")
    
    # Get some ticker prices
    popular_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    print("\n📊 Current Prices:")
    
    for symbol in popular_symbols:
        ticker = client.get_ticker_price(symbol)
        if "price" in ticker:
            print(f"   {symbol}: ${float(ticker['price']):,.2f}")
    
    # Test account info if keys are provided
    if client.api_key and client.secret_key:
        print("\n💰 Account Info:")
        account = client.get_account_info()
        if "error" not in account:
            print("✅ Account access - OK")
            balances = [b for b in account.get("balances", []) if float(b["free"]) > 0]
            if balances:
                print("   Balances:")
                for balance in balances[:5]:  # Show first 5
                    print(f"     {balance['asset']}: {balance['free']}")
        else:
            print(f"❌ Account access failed: {account['error']}")
    else:
        print("\n⚠️ No API keys configured - account features disabled")
        print("   Add BINANCE_API_KEY and BINANCE_SECRET_KEY to .env file")
    
    return True

if __name__ == "__main__":
    test_binance_testnet()