#!/usr/bin/env python3
"""
Simple Backend for AI Trading System v2.0
Optimized for Mac M2 - No complex dependencies
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# FastAPI and basic dependencies
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Trading System API",
    description="Simple backend for AI Trading System v2.0",
    version="2.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage for demo
trading_data = {
    "balance": 10000.0,
    "positions": [],
    "orders": [],
    "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]
}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Trading System API v2.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "system": "Mac M2 Optimized"
    }

@app.get("/api/status")
async def get_status():
    """Get system status"""
    return {
        "status": "active",
        "mode": "testnet",
        "exchange": "binance_testnet",
        "balance": trading_data["balance"],
        "active_positions": len(trading_data["positions"]),
        "pending_orders": len(trading_data["orders"])
    }

@app.get("/api/balance")
async def get_balance():
    """Get account balance"""
    return {
        "balance": trading_data["balance"],
        "currency": "USDT",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/symbols")
async def get_symbols():
    """Get available trading symbols"""
    return {
        "symbols": trading_data["symbols"],
        "count": len(trading_data["symbols"])
    }

@app.get("/api/market/symbols")
async def get_market_symbols():
    """Get market symbols with mock data"""
    symbols_data = []
    for symbol in trading_data["symbols"]:
        # Mock price data
        base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 100
        symbols_data.append({
            "symbol": symbol,
            "price": base_price + (hash(symbol) % 1000),
            "change_24h": (hash(symbol) % 10) - 5,
            "volume": hash(symbol) % 1000000
        })
    
    return {
        "symbols": symbols_data,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/positions")
async def get_positions():
    """Get current positions"""
    return {
        "positions": trading_data["positions"],
        "count": len(trading_data["positions"])
    }

@app.get("/api/orders")
async def get_orders():
    """Get current orders"""
    return {
        "orders": trading_data["orders"],
        "count": len(trading_data["orders"])
    }

@app.post("/api/orders")
async def create_order(order_data: dict):
    """Create a new order (mock)"""
    order = {
        "id": len(trading_data["orders"]) + 1,
        "symbol": order_data.get("symbol", "BTCUSDT"),
        "side": order_data.get("side", "buy"),
        "amount": order_data.get("amount", 0.001),
        "price": order_data.get("price", 50000),
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }
    
    trading_data["orders"].append(order)
    
    return {
        "message": "Order created successfully",
        "order": order
    }

@app.get("/api/config")
async def get_config():
    """Get system configuration"""
    return {
        "exchange": "binance",
        "mode": "testnet",
        "api_key_set": True,  # Mock
        "websocket_enabled": False,
        "auto_trading": False
    }

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint for connectivity"""
    return {
        "message": "Backend is working!",
        "backend": "Python FastAPI",
        "frontend": "React + Vite",
        "platform": "Mac M2",
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "Endpoint not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "error": str(exc)}
    )

def main():
    """Main function to run the server"""
    print("🚀 Starting AI Trading System Backend v2.0")
    print("📱 Optimized for Mac M2")
    print("🔗 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("❤️ Health: http://localhost:8000/api/health")
    print("-" * 50)
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Backend stopped!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()