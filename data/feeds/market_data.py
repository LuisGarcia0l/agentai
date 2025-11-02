"""
📊 Market Data Manager

Gestor centralizado de datos de mercado con múltiples fuentes.
Soporta Binance, Yahoo Finance, Alpaca y más.
"""

import asyncio
import ccxt
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from utils.config.settings import settings
from utils.logging.logger import trading_logger
import aiohttp


@dataclass
class OHLCV:
    """Estructura de datos OHLCV."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str


@dataclass
class Ticker:
    """Información de ticker."""
    symbol: str
    price: float
    bid: float
    ask: float
    volume: float
    change_24h: float
    timestamp: datetime


class MarketDataManager:
    """Gestor principal de datos de mercado."""
    
    def __init__(self):
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, any] = {}
        self.cache_ttl: Dict[str, datetime] = {}
        
    async def initialize(self):
        """Inicializar conexiones con exchanges."""
        trading_logger.logger.info("🔌 Inicializando conexiones de datos...")
        
        # Crear sesión HTTP
        self.session = aiohttp.ClientSession()
        
        # Inicializar Binance
        if settings.BINANCE_API_KEY:
            await self._init_binance()
        
        # Inicializar otros exchanges según configuración
        trading_logger.logger.info("✅ Conexiones de datos inicializadas")
    
    async def _init_binance(self):
        """Inicializar conexión con Binance."""
        try:
            config = settings.get_exchange_config("binance")
            
            self.exchanges["binance"] = ccxt.binance({
                'apiKey': config.get('api_key'),
                'secret': config.get('secret'),
                'sandbox': config.get('testnet', True),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'  # spot, margin, future
                }
            })
            
            # Verificar conexión
            await self.exchanges["binance"].load_markets()
            trading_logger.logger.info("✅ Binance conectado correctamente")
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error conectando Binance: {e}")
    
    async def get_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = '1h',
        limit: int = 100,
        exchange: str = "binance"
    ) -> List[OHLCV]:
        """
        Obtener datos OHLCV.
        
        Args:
            symbol: Símbolo del activo (ej: 'BTC/USDT')
            timeframe: Marco temporal ('1m', '5m', '1h', '1d')
            limit: Número de velas
            exchange: Exchange a usar
        
        Returns:
            Lista de datos OHLCV
        """
        cache_key = f"{exchange}_{symbol}_{timeframe}_{limit}"
        
        # Verificar cache
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        try:
            if exchange in self.exchanges:
                # Usar CCXT para exchanges
                ohlcv_data = await self.exchanges[exchange].fetch_ohlcv(
                    symbol, timeframe, limit=limit
                )
                
                result = [
                    OHLCV(
                        timestamp=datetime.fromtimestamp(candle[0] / 1000),
                        open=candle[1],
                        high=candle[2],
                        low=candle[3],
                        close=candle[4],
                        volume=candle[5],
                        symbol=symbol
                    )
                    for candle in ohlcv_data
                ]
            else:
                # Usar Yahoo Finance como fallback
                result = await self._get_yahoo_ohlcv(symbol, timeframe, limit)
            
            # Guardar en cache
            self._cache_data(cache_key, result, ttl_minutes=5)
            
            trading_logger.logger.debug(
                f"📊 Obtenidos {len(result)} datos OHLCV para {symbol}"
            )
            
            return result
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error obteniendo OHLCV {symbol}: {e}")
            return []
    
    async def _get_yahoo_ohlcv(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int
    ) -> List[OHLCV]:
        """Obtener datos OHLCV de Yahoo Finance."""
        try:
            # Convertir símbolo para Yahoo Finance
            yahoo_symbol = symbol.replace('/', '-')
            
            # Calcular período
            period_map = {
                '1m': '1d',
                '5m': '5d', 
                '1h': '1mo',
                '1d': '1y'
            }
            period = period_map.get(timeframe, '1mo')
            
            # Obtener datos
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period=period, interval=timeframe)
            
            if hist.empty:
                return []
            
            # Convertir a formato OHLCV
            result = []
            for timestamp, row in hist.tail(limit).iterrows():
                result.append(OHLCV(
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=float(row['Volume']),
                    symbol=symbol
                ))
            
            return result
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error Yahoo Finance {symbol}: {e}")
            return []
    
    async def get_ticker(self, symbol: str, exchange: str = "binance") -> Optional[Ticker]:
        """
        Obtener información de ticker actual.
        
        Args:
            symbol: Símbolo del activo
            exchange: Exchange a usar
        
        Returns:
            Información del ticker
        """
        cache_key = f"ticker_{exchange}_{symbol}"
        
        # Verificar cache (TTL corto para tickers)
        if self._is_cached(cache_key, ttl_minutes=1):
            return self.cache[cache_key]
        
        try:
            if exchange in self.exchanges:
                ticker_data = await self.exchanges[exchange].fetch_ticker(symbol)
                
                result = Ticker(
                    symbol=symbol,
                    price=ticker_data['last'],
                    bid=ticker_data['bid'] or ticker_data['last'],
                    ask=ticker_data['ask'] or ticker_data['last'],
                    volume=ticker_data['baseVolume'],
                    change_24h=ticker_data['percentage'] or 0,
                    timestamp=datetime.now()
                )
                
                # Guardar en cache
                self._cache_data(cache_key, result, ttl_minutes=1)
                
                return result
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error obteniendo ticker {symbol}: {e}")
        
        return None
    
    async def get_orderbook(
        self, 
        symbol: str, 
        limit: int = 20,
        exchange: str = "binance"
    ) -> Optional[Dict]:
        """
        Obtener libro de órdenes.
        
        Args:
            symbol: Símbolo del activo
            limit: Número de niveles
            exchange: Exchange a usar
        
        Returns:
            Libro de órdenes con bids y asks
        """
        try:
            if exchange in self.exchanges:
                orderbook = await self.exchanges[exchange].fetch_order_book(
                    symbol, limit
                )
                return orderbook
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error obteniendo orderbook {symbol}: {e}")
        
        return None
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = '1h',
        exchange: str = "binance"
    ) -> pd.DataFrame:
        """
        Obtener datos históricos para backtesting.
        
        Args:
            symbol: Símbolo del activo
            start_date: Fecha de inicio
            end_date: Fecha de fin
            timeframe: Marco temporal
            exchange: Exchange a usar
        
        Returns:
            DataFrame con datos históricos
        """
        try:
            # Calcular número de velas necesarias
            timeframe_minutes = {
                '1m': 1, '5m': 5, '15m': 15, '30m': 30,
                '1h': 60, '4h': 240, '1d': 1440
            }
            
            minutes = timeframe_minutes.get(timeframe, 60)
            total_minutes = int((end_date - start_date).total_seconds() / 60)
            limit = min(total_minutes // minutes, 1000)  # Límite de API
            
            # Obtener datos
            ohlcv_data = await self.get_ohlcv(symbol, timeframe, limit, exchange)
            
            if not ohlcv_data:
                return pd.DataFrame()
            
            # Convertir a DataFrame
            data = []
            for candle in ohlcv_data:
                if start_date <= candle.timestamp <= end_date:
                    data.append({
                        'timestamp': candle.timestamp,
                        'open': candle.open,
                        'high': candle.high,
                        'low': candle.low,
                        'close': candle.close,
                        'volume': candle.volume
                    })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
            
            trading_logger.logger.info(
                f"📈 Datos históricos obtenidos: {len(df)} velas para {symbol}"
            )
            
            return df
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error datos históricos {symbol}: {e}")
            return pd.DataFrame()
    
    def _is_cached(self, key: str, ttl_minutes: int = 5) -> bool:
        """Verificar si los datos están en cache y son válidos."""
        if key not in self.cache:
            return False
        
        if key not in self.cache_ttl:
            return False
        
        expiry = self.cache_ttl[key]
        return datetime.now() < expiry
    
    def _cache_data(self, key: str, data: any, ttl_minutes: int = 5):
        """Guardar datos en cache con TTL."""
        self.cache[key] = data
        self.cache_ttl[key] = datetime.now() + timedelta(minutes=ttl_minutes)
    
    async def close(self):
        """Cerrar conexiones."""
        trading_logger.logger.info("🔌 Cerrando conexiones de datos...")
        
        # Cerrar exchanges
        for exchange in self.exchanges.values():
            if hasattr(exchange, 'close'):
                await exchange.close()
        
        # Cerrar sesión HTTP
        if self.session:
            await self.session.close()
        
        trading_logger.logger.info("✅ Conexiones cerradas")


# Instancia global
market_data_manager = MarketDataManager()