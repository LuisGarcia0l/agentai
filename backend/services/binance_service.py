"""
Servicio para interactuar con Binance Testnet
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta

from backend.core.config import settings

class BinanceService:
    """
    Servicio para interactuar con Binance Testnet API
    
    Funcionalidades:
    - Obtener datos de mercado en tiempo real
    - Ejecutar órdenes de compra/venta
    - Gestionar información de cuenta
    - Obtener datos históricos para backtesting
    """
    
    def __init__(self):
        self.logger = logging.getLogger("services.binance")
        self.base_url = settings.BINANCE_TESTNET_BASE_URL
        self.api_key = settings.BINANCE_TESTNET_API_KEY
        self.secret_key = settings.BINANCE_TESTNET_SECRET_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_initialized = False
        
    async def initialize(self):
        """Inicializar el servicio"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Verificar conectividad
            if self.api_key and self.secret_key:
                account_info = await self.get_account_info()
                if account_info:
                    self.logger.info("✅ Conectado a Binance Testnet")
                    self.is_initialized = True
                else:
                    self.logger.warning("⚠️ Credenciales de Binance no válidas, usando modo simulación")
                    self.is_initialized = True  # Permitir modo simulación
            else:
                self.logger.warning("⚠️ Credenciales de Binance no configuradas, usando modo simulación")
                self.is_initialized = True  # Permitir modo simulación
                
        except Exception as e:
            self.logger.error(f"Error inicializando Binance service: {e}")
            self.is_initialized = True  # Permitir modo simulación
    
    async def close(self):
        """Cerrar el servicio"""
        if self.session:
            await self.session.close()
    
    def _generate_signature(self, query_string: str) -> str:
        """Generar firma HMAC para autenticación"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para requests autenticados"""
        return {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
    
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Optional[Dict]:
        """Hacer request a la API de Binance"""
        if not self.session:
            return None
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if params is None:
            params = {}
        
        try:
            if signed:
                # Agregar timestamp
                params['timestamp'] = int(time.time() * 1000)
                
                # Crear query string
                query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                
                # Generar firma
                signature = self._generate_signature(query_string)
                params['signature'] = signature
                
                headers = self._get_headers()
            
            if method.upper() == 'GET':
                async with self.session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.error(f"Error en request: {response.status} - {await response.text()}")
                        return None
            
            elif method.upper() == 'POST':
                async with self.session.post(url, data=params, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.error(f"Error en request: {response.status} - {await response.text()}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error en request a {endpoint}: {e}")
            return None
    
    async def get_server_time(self) -> Optional[int]:
        """Obtener tiempo del servidor"""
        result = await self._make_request('GET', '/api/v3/time')
        return result.get('serverTime') if result else None
    
    async def get_exchange_info(self) -> Optional[Dict]:
        """Obtener información del exchange"""
        return await self._make_request('GET', '/api/v3/exchangeInfo')
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Obtener precio actual de un símbolo"""
        try:
            result = await self._make_request('GET', '/api/v3/ticker/price', {'symbol': symbol})
            if result and 'price' in result:
                return float(result['price'])
            
            # Fallback: usar datos simulados si no hay conexión real
            return await self._get_simulated_price(symbol)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo precio de {symbol}: {e}")
            return await self._get_simulated_price(symbol)
    
    async def _get_simulated_price(self, symbol: str) -> float:
        """Generar precio simulado para testing"""
        import random
        
        # Precios base simulados
        base_prices = {
            'BTCUSDT': 45000.0,
            'ETHUSDT': 3000.0,
            'ADAUSDT': 0.5,
            'DOTUSDT': 7.0,
            'LINKUSDT': 15.0,
            'BNBUSDT': 300.0,
            'SOLUSDT': 100.0,
            'MATICUSDT': 0.8,
            'AVAXUSDT': 25.0,
            'ATOMUSDT': 12.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        # Agregar variación aleatoria del ±2%
        variation = random.uniform(-0.02, 0.02)
        return base_price * (1 + variation)
    
    async def get_24hr_ticker(self, symbol: str) -> Optional[Dict]:
        """Obtener estadísticas de 24 horas"""
        try:
            result = await self._make_request('GET', '/api/v3/ticker/24hr', {'symbol': symbol})
            if result:
                return result
            
            # Fallback simulado
            current_price = await self._get_simulated_price(symbol)
            return {
                'symbol': symbol,
                'priceChange': str(current_price * 0.02),  # 2% cambio simulado
                'priceChangePercent': '2.00',
                'weightedAvgPrice': str(current_price),
                'prevClosePrice': str(current_price * 0.98),
                'lastPrice': str(current_price),
                'lastQty': '1.00000000',
                'bidPrice': str(current_price * 0.999),
                'askPrice': str(current_price * 1.001),
                'openPrice': str(current_price * 0.98),
                'highPrice': str(current_price * 1.05),
                'lowPrice': str(current_price * 0.95),
                'volume': '1000.00000000',
                'quoteVolume': str(current_price * 1000),
                'openTime': int((datetime.utcnow() - timedelta(days=1)).timestamp() * 1000),
                'closeTime': int(datetime.utcnow().timestamp() * 1000),
                'count': 1000
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ticker de {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
        """
        Obtener datos históricos (klines)
        
        Args:
            symbol: Símbolo de trading (ej: BTCUSDT)
            interval: Intervalo de tiempo (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Número de velas (máximo 1000)
        """
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': min(limit, 1000)
            }
            
            result = await self._make_request('GET', '/api/v3/klines', params)
            
            if result:
                # Convertir a DataFrame
                df = pd.DataFrame(result, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                
                # Convertir tipos de datos
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col])
                
                df.set_index('timestamp', inplace=True)
                return df[['open', 'high', 'low', 'close', 'volume']]
            
            # Fallback: generar datos simulados
            return await self._generate_simulated_data(symbol, interval, limit)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos históricos de {symbol}: {e}")
            return await self._generate_simulated_data(symbol, interval, limit)
    
    async def _generate_simulated_data(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        """Generar datos históricos simulados para testing"""
        import numpy as np
        
        # Mapear intervalos a minutos
        interval_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        
        minutes = interval_minutes.get(interval, 60)
        
        # Generar timestamps
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes * limit)
        timestamps = pd.date_range(start=start_time, end=end_time, freq=f'{minutes}min')[:limit]
        
        # Precio base
        base_price = await self._get_simulated_price(symbol)
        
        # Generar datos usando random walk
        np.random.seed(42)  # Para reproducibilidad
        returns = np.random.normal(0, 0.02, limit)  # 2% volatilidad
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Crear OHLCV
        data = []
        for i, (timestamp, price) in enumerate(zip(timestamps, prices)):
            # Generar high/low alrededor del precio
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            
            # Open es el close anterior (excepto el primero)
            open_price = prices[i-1] if i > 0 else price
            close_price = price
            
            # Volumen simulado
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': max(open_price, high, close_price),
                'low': min(open_price, low, close_price),
                'close': close_price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    async def get_account_info(self) -> Optional[Dict]:
        """Obtener información de la cuenta"""
        if not self.api_key or not self.secret_key:
            # Retornar información simulada
            return {
                'makerCommission': 10,
                'takerCommission': 10,
                'buyerCommission': 0,
                'sellerCommission': 0,
                'canTrade': True,
                'canWithdraw': True,
                'canDeposit': True,
                'updateTime': int(time.time() * 1000),
                'accountType': 'SPOT',
                'balances': [
                    {'asset': 'USDT', 'free': '1000.00000000', 'locked': '0.00000000'},
                    {'asset': 'BTC', 'free': '0.00000000', 'locked': '0.00000000'},
                    {'asset': 'ETH', 'free': '0.00000000', 'locked': '0.00000000'}
                ]
            }
        
        return await self._make_request('GET', '/api/v3/account', signed=True)
    
    async def place_order(self, symbol: str, side: str, order_type: str, 
                         quantity: float, price: float = None, **kwargs) -> Dict[str, Any]:
        """
        Colocar una orden
        
        Args:
            symbol: Símbolo de trading
            side: BUY o SELL
            order_type: MARKET, LIMIT, STOP_LOSS_LIMIT, etc.
            quantity: Cantidad
            price: Precio (requerido para órdenes LIMIT)
        """
        try:
            if not self.api_key or not self.secret_key:
                # Modo simulación
                return await self._simulate_order(symbol, side, order_type, quantity, price)
            
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': f"{quantity:.8f}",
                'timeInForce': kwargs.get('timeInForce', 'GTC')
            }
            
            if order_type in ['LIMIT', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT']:
                if price is None:
                    raise ValueError(f"Precio requerido para orden {order_type}")
                params['price'] = f"{price:.8f}"
            
            if order_type in ['STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT']:
                stop_price = kwargs.get('stopPrice')
                if stop_price is None:
                    raise ValueError(f"stopPrice requerido para orden {order_type}")
                params['stopPrice'] = f"{stop_price:.8f}"
            
            result = await self._make_request('POST', '/api/v3/order', params, signed=True)
            
            if result:
                return {
                    'success': True,
                    'order_id': result.get('orderId'),
                    'status': result.get('status'),
                    'executed_quantity': float(result.get('executedQty', 0)),
                    'executed_price': float(result.get('price', price or 0)),
                    'result': result
                }
            else:
                return {
                    'success': False,
                    'error': 'Error colocando orden'
                }
                
        except Exception as e:
            self.logger.error(f"Error colocando orden: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _simulate_order(self, symbol: str, side: str, order_type: str, 
                            quantity: float, price: float = None) -> Dict[str, Any]:
        """Simular ejecución de orden para testing"""
        try:
            current_price = await self.get_current_price(symbol)
            if not current_price:
                current_price = 100.0  # Precio por defecto
            
            executed_price = price if price else current_price
            
            # Simular slippage pequeño para órdenes de mercado
            if order_type == 'MARKET':
                slippage = 0.001  # 0.1%
                if side == 'BUY':
                    executed_price = current_price * (1 + slippage)
                else:
                    executed_price = current_price * (1 - slippage)
            
            return {
                'success': True,
                'order_id': f"sim_{int(time.time() * 1000)}",
                'status': 'FILLED',
                'executed_quantity': quantity,
                'executed_price': executed_price,
                'result': {
                    'symbol': symbol,
                    'orderId': f"sim_{int(time.time() * 1000)}",
                    'orderListId': -1,
                    'clientOrderId': f"sim_client_{int(time.time())}",
                    'transactTime': int(time.time() * 1000),
                    'price': str(executed_price),
                    'origQty': str(quantity),
                    'executedQty': str(quantity),
                    'cummulativeQuoteQty': str(quantity * executed_price),
                    'status': 'FILLED',
                    'timeInForce': 'GTC',
                    'type': order_type,
                    'side': side
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error simulando orden: {str(e)}"
            }
    
    async def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Cancelar una orden"""
        try:
            if not self.api_key or not self.secret_key:
                # Simulación
                return {
                    'success': True,
                    'message': f'Orden {order_id} cancelada (simulación)'
                }
            
            params = {
                'symbol': symbol,
                'orderId': order_id
            }
            
            result = await self._make_request('DELETE', '/api/v3/order', params, signed=True)
            
            if result:
                return {
                    'success': True,
                    'result': result
                }
            else:
                return {
                    'success': False,
                    'error': 'Error cancelando orden'
                }
                
        except Exception as e:
            self.logger.error(f"Error cancelando orden: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_order_status(self, symbol: str, order_id: str) -> Optional[Dict]:
        """Obtener estado de una orden"""
        try:
            if not self.api_key or not self.secret_key:
                # Simulación - asumir que todas las órdenes están completadas
                return {
                    'symbol': symbol,
                    'orderId': order_id,
                    'status': 'FILLED',
                    'executedQty': '1.0',
                    'price': '100.0'
                }
            
            params = {
                'symbol': symbol,
                'orderId': order_id
            }
            
            return await self._make_request('GET', '/api/v3/order', params, signed=True)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de orden: {e}")
            return None
    
    async def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Obtener órdenes abiertas"""
        try:
            if not self.api_key or not self.secret_key:
                return []  # Sin órdenes abiertas en simulación
            
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            result = await self._make_request('GET', '/api/v3/openOrders', params, signed=True)
            return result if result else []
            
        except Exception as e:
            self.logger.error(f"Error obteniendo órdenes abiertas: {e}")
            return []
    
    async def get_trade_history(self, symbol: str, limit: int = 500) -> List[Dict]:
        """Obtener historial de trades"""
        try:
            if not self.api_key or not self.secret_key:
                return []  # Sin historial en simulación
            
            params = {
                'symbol': symbol,
                'limit': min(limit, 1000)
            }
            
            result = await self._make_request('GET', '/api/v3/myTrades', params, signed=True)
            return result if result else []
            
        except Exception as e:
            self.logger.error(f"Error obteniendo historial de trades: {e}")
            return []