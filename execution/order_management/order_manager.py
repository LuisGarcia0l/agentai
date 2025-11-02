"""
💼 Order Manager - Gestor de Órdenes Avanzado

Sistema completo de gestión de órdenes que maneja ejecución,
seguimiento y optimización de trades en múltiples exchanges.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from data.feeds.market_data import MarketDataManager
from risk_management.portfolio.risk_manager import RiskManager
from utils.config.settings import Settings
from utils.logging.logger import trading_logger


class OrderType(Enum):
    """Tipos de órdenes."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    """Lado de la orden."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Estados de órdenes."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(Enum):
    """Tiempo en vigor de la orden."""
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill
    DAY = "day"  # Day order


@dataclass
class Order:
    """Orden de trading."""
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    status: OrderStatus = OrderStatus.PENDING
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Ejecución
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    commission: float = 0.0
    
    # Metadatos
    exchange: str = "binance"
    client_order_id: Optional[str] = None
    exchange_order_id: Optional[str] = None
    parent_order_id: Optional[str] = None  # Para órdenes OCO
    
    # Configuración adicional
    reduce_only: bool = False
    post_only: bool = False
    
    @property
    def is_active(self) -> bool:
        """Verificar si la orden está activa."""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
    
    @property
    def is_filled(self) -> bool:
        """Verificar si la orden está completamente ejecutada."""
        return self.status == OrderStatus.FILLED
    
    @property
    def remaining_quantity(self) -> float:
        """Cantidad restante por ejecutar."""
        return self.quantity - self.filled_quantity


@dataclass
class Fill:
    """Ejecución parcial de una orden."""
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float
    timestamp: datetime = field(default_factory=datetime.now)
    trade_id: Optional[str] = None


@dataclass
class Position:
    """Posición de trading."""
    symbol: str
    size: float = 0.0  # Positivo = largo, Negativo = corto
    avg_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)
    
    @property
    def is_long(self) -> bool:
        return self.size > 0
    
    @property
    def is_short(self) -> bool:
        return self.size < 0
    
    @property
    def is_flat(self) -> bool:
        return abs(self.size) < 1e-8
    
    @property
    def market_value(self) -> float:
        return abs(self.size * self.avg_price)


class OrderManager:
    """Gestor principal de órdenes."""
    
    def __init__(
        self,
        market_data: MarketDataManager,
        risk_manager: RiskManager,
        settings: Settings
    ):
        self.market_data = market_data
        self.risk_manager = risk_manager
        self.settings = settings
        
        # Estado interno
        self.orders: Dict[str, Order] = {}
        self.fills: Dict[str, Fill] = {}
        self.positions: Dict[str, Position] = {}
        
        # Callbacks
        self.order_callbacks: List[Callable] = []
        self.fill_callbacks: List[Callable] = []
        self.position_callbacks: List[Callable] = []
        
        # Configuración
        self.commission_rate = 0.001  # 0.1%
        self.slippage_rate = 0.0001   # 0.01%
        
        # Estado del manager
        self.is_running = False
        self.last_update = datetime.now()
    
    async def initialize(self):
        """Inicializar el gestor de órdenes."""
        trading_logger.logger.info("💼 Inicializando Order Manager...")
        
        # Cargar estado previo si existe
        await self._load_state()
        
        self.is_running = True
        trading_logger.logger.info("✅ Order Manager inicializado")
    
    async def submit_order(self, order: Order) -> bool:
        """
        Enviar orden al mercado.
        
        Args:
            order: Orden a enviar
        
        Returns:
            True si la orden fue enviada exitosamente
        """
        try:
            # Validar orden
            validation_result = await self._validate_order(order)
            if not validation_result[0]:
                trading_logger.logger.warning(f"⚠️ Orden rechazada: {validation_result[1]}")
                order.status = OrderStatus.REJECTED
                return False
            
            # Generar IDs
            if not order.client_order_id:
                order.client_order_id = f"order_{uuid.uuid4().hex[:8]}"
            
            # Simular envío al exchange
            if self.settings.TRADING_MODE == "paper":
                success = await self._submit_paper_order(order)
            else:
                success = await self._submit_live_order(order)
            
            if success:
                order.status = OrderStatus.SUBMITTED
                order.submitted_at = datetime.now()
                self.orders[order.id] = order
                
                # Notificar callbacks
                await self._notify_order_callbacks(order, "submitted")
                
                trading_logger.trade_executed(
                    symbol=order.symbol,
                    action=order.side.value,
                    quantity=order.quantity,
                    price=order.price or 0.0,
                    order_id=order.id
                )
                
                return True
            else:
                order.status = OrderStatus.REJECTED
                return False
                
        except Exception as e:
            trading_logger.logger.error(f"❌ Error enviando orden {order.id}: {e}")
            order.status = OrderStatus.REJECTED
            return False
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancelar una orden.
        
        Args:
            order_id: ID de la orden a cancelar
        
        Returns:
            True si la orden fue cancelada exitosamente
        """
        try:
            if order_id not in self.orders:
                trading_logger.logger.warning(f"⚠️ Orden {order_id} no encontrada")
                return False
            
            order = self.orders[order_id]
            
            if not order.is_active:
                trading_logger.logger.warning(f"⚠️ Orden {order_id} no está activa")
                return False
            
            # Simular cancelación
            if self.settings.TRADING_MODE == "paper":
                success = await self._cancel_paper_order(order)
            else:
                success = await self._cancel_live_order(order)
            
            if success:
                order.status = OrderStatus.CANCELLED
                await self._notify_order_callbacks(order, "cancelled")
                
                trading_logger.logger.info(f"🚫 Orden {order_id} cancelada")
                return True
            
            return False
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error cancelando orden {order_id}: {e}")
            return False
    
    async def modify_order(
        self,
        order_id: str,
        new_quantity: Optional[float] = None,
        new_price: Optional[float] = None
    ) -> bool:
        """
        Modificar una orden existente.
        
        Args:
            order_id: ID de la orden
            new_quantity: Nueva cantidad
            new_price: Nuevo precio
        
        Returns:
            True si la orden fue modificada exitosamente
        """
        try:
            if order_id not in self.orders:
                return False
            
            order = self.orders[order_id]
            
            if not order.is_active:
                return False
            
            # Cancelar orden original
            cancel_success = await self.cancel_order(order_id)
            if not cancel_success:
                return False
            
            # Crear nueva orden modificada
            new_order = Order(
                id=f"mod_{uuid.uuid4().hex[:8]}",
                symbol=order.symbol,
                side=order.side,
                type=order.type,
                quantity=new_quantity or order.quantity,
                price=new_price or order.price,
                stop_price=order.stop_price,
                time_in_force=order.time_in_force,
                exchange=order.exchange,
                parent_order_id=order_id
            )
            
            # Enviar nueva orden
            return await self.submit_order(new_order)
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error modificando orden {order_id}: {e}")
            return False
    
    async def create_bracket_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        entry_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> List[str]:
        """
        Crear orden bracket (entrada + stop loss + take profit).
        
        Args:
            symbol: Símbolo del activo
            side: Lado de la orden (buy/sell)
            quantity: Cantidad
            entry_price: Precio de entrada (None para market order)
            stop_loss_price: Precio de stop loss
            take_profit_price: Precio de take profit
        
        Returns:
            Lista de IDs de órdenes creadas
        """
        try:
            order_ids = []
            
            # Orden de entrada
            entry_order = Order(
                id=f"entry_{uuid.uuid4().hex[:8]}",
                symbol=symbol,
                side=side,
                type=OrderType.MARKET if entry_price is None else OrderType.LIMIT,
                quantity=quantity,
                price=entry_price
            )
            
            if await self.submit_order(entry_order):
                order_ids.append(entry_order.id)
                
                # Esperar a que se ejecute la orden de entrada
                await self._wait_for_fill(entry_order.id, timeout=60)
                
                if entry_order.is_filled:
                    # Crear órdenes de salida
                    exit_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
                    
                    # Stop loss
                    if stop_loss_price:
                        stop_order = Order(
                            id=f"stop_{uuid.uuid4().hex[:8]}",
                            symbol=symbol,
                            side=exit_side,
                            type=OrderType.STOP,
                            quantity=quantity,
                            stop_price=stop_loss_price,
                            parent_order_id=entry_order.id,
                            reduce_only=True
                        )
                        
                        if await self.submit_order(stop_order):
                            order_ids.append(stop_order.id)
                    
                    # Take profit
                    if take_profit_price:
                        profit_order = Order(
                            id=f"profit_{uuid.uuid4().hex[:8]}",
                            symbol=symbol,
                            side=exit_side,
                            type=OrderType.LIMIT,
                            quantity=quantity,
                            price=take_profit_price,
                            parent_order_id=entry_order.id,
                            reduce_only=True
                        )
                        
                        if await self.submit_order(profit_order):
                            order_ids.append(profit_order.id)
            
            return order_ids
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error creando bracket order: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """
        Obtener posición actual de un símbolo.
        
        Args:
            symbol: Símbolo del activo
        
        Returns:
            Posición actual o None
        """
        return self.positions.get(symbol)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Obtener órdenes abiertas.
        
        Args:
            symbol: Filtrar por símbolo (opcional)
        
        Returns:
            Lista de órdenes abiertas
        """
        orders = [order for order in self.orders.values() if order.is_active]
        
        if symbol:
            orders = [order for order in orders if order.symbol == symbol]
        
        return orders
    
    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """
        Obtener historial de órdenes.
        
        Args:
            symbol: Filtrar por símbolo (opcional)
            limit: Número máximo de órdenes
        
        Returns:
            Lista de órdenes históricas
        """
        orders = list(self.orders.values())
        
        if symbol:
            orders = [order for order in orders if order.symbol == symbol]
        
        # Ordenar por fecha de creación (más recientes primero)
        orders.sort(key=lambda x: x.created_at, reverse=True)
        
        return orders[:limit]
    
    async def _validate_order(self, order: Order) -> tuple[bool, str]:
        """Validar orden antes de enviar."""
        try:
            # Validaciones básicas
            if order.quantity <= 0:
                return False, "Cantidad debe ser positiva"
            
            if order.type == OrderType.LIMIT and order.price is None:
                return False, "Precio requerido para orden limit"
            
            if order.type in [OrderType.STOP, OrderType.STOP_LIMIT] and order.stop_price is None:
                return False, "Stop price requerido para orden stop"
            
            # Validar con risk manager
            current_positions = {
                symbol: {
                    'size': pos.size,
                    'price': pos.avg_price,
                    'entry_price': pos.avg_price,
                    'current_price': pos.avg_price  # Simplificado
                }
                for symbol, pos in self.positions.items()
            }
            
            # Simular valor del portafolio
            portfolio_value = self.settings.BACKTEST_INITIAL_CAPITAL
            
            if order.side == OrderSide.BUY:
                can_open, reason = self.risk_manager.should_open_position(
                    symbol=order.symbol,
                    position_size=order.quantity,
                    entry_price=order.price or 0,
                    portfolio_value=portfolio_value,
                    current_positions=current_positions
                )
                
                if not can_open:
                    return False, f"Risk manager: {reason}"
            
            return True, "Orden válida"
            
        except Exception as e:
            return False, f"Error en validación: {e}"
    
    async def _submit_paper_order(self, order: Order) -> bool:
        """Simular envío de orden en paper trading."""
        try:
            # Simular latencia
            await asyncio.sleep(0.1)
            
            # En paper trading, las órdenes market se ejecutan inmediatamente
            if order.type == OrderType.MARKET:
                await self._simulate_fill(order)
            
            return True
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error en paper order: {e}")
            return False
    
    async def _submit_live_order(self, order: Order) -> bool:
        """Enviar orden real al exchange."""
        # TODO: Implementar conexión real con exchange
        trading_logger.logger.warning("⚠️ Live trading no implementado aún")
        return False
    
    async def _cancel_paper_order(self, order: Order) -> bool:
        """Simular cancelación en paper trading."""
        await asyncio.sleep(0.05)  # Simular latencia
        return True
    
    async def _cancel_live_order(self, order: Order) -> bool:
        """Cancelar orden real en exchange."""
        # TODO: Implementar cancelación real
        trading_logger.logger.warning("⚠️ Live trading no implementado aún")
        return False
    
    async def _simulate_fill(self, order: Order):
        """Simular ejecución de orden."""
        try:
            # Obtener precio actual
            ticker = await self.market_data.get_ticker(order.symbol)
            if not ticker:
                return
            
            # Determinar precio de ejecución
            if order.type == OrderType.MARKET:
                if order.side == OrderSide.BUY:
                    fill_price = ticker.ask * (1 + self.slippage_rate)
                else:
                    fill_price = ticker.bid * (1 - self.slippage_rate)
            else:
                fill_price = order.price
            
            # Crear fill
            fill = Fill(
                id=f"fill_{uuid.uuid4().hex[:8]}",
                order_id=order.id,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=fill_price,
                commission=order.quantity * fill_price * self.commission_rate
            )
            
            # Actualizar orden
            order.filled_quantity = order.quantity
            order.avg_fill_price = fill_price
            order.commission = fill.commission
            order.status = OrderStatus.FILLED
            order.filled_at = datetime.now()
            
            # Guardar fill
            self.fills[fill.id] = fill
            
            # Actualizar posición
            await self._update_position(fill)
            
            # Notificar callbacks
            await self._notify_fill_callbacks(fill)
            await self._notify_order_callbacks(order, "filled")
            
            trading_logger.logger.info(
                f"✅ Orden ejecutada: {order.side.value} {order.quantity} {order.symbol} @ ${fill_price:.2f}"
            )
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error simulando fill: {e}")
    
    async def _update_position(self, fill: Fill):
        """Actualizar posición basada en fill."""
        try:
            symbol = fill.symbol
            
            if symbol not in self.positions:
                self.positions[symbol] = Position(symbol=symbol)
            
            position = self.positions[symbol]
            
            # Calcular nueva posición
            if fill.side == OrderSide.BUY:
                new_size = position.size + fill.quantity
            else:
                new_size = position.size - fill.quantity
            
            # Actualizar precio promedio
            if new_size != 0:
                if (position.size > 0 and fill.side == OrderSide.BUY) or \
                   (position.size < 0 and fill.side == OrderSide.SELL):
                    # Aumentar posición existente
                    total_cost = (position.size * position.avg_price + 
                                 fill.quantity * fill.price)
                    position.avg_price = total_cost / new_size
                else:
                    # Cambiar dirección o cerrar posición
                    if abs(new_size) < abs(position.size):
                        # Reducir posición - mantener precio promedio
                        pass
                    else:
                        # Nueva posición en dirección opuesta
                        position.avg_price = fill.price
            
            position.size = new_size
            position.last_update = datetime.now()
            
            # Notificar callbacks
            await self._notify_position_callbacks(position)
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error actualizando posición: {e}")
    
    async def _wait_for_fill(self, order_id: str, timeout: int = 60) -> bool:
        """Esperar a que se ejecute una orden."""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            if order_id in self.orders:
                order = self.orders[order_id]
                if order.is_filled:
                    return True
                if order.status in [OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                    return False
            
            await asyncio.sleep(0.5)
        
        return False
    
    async def _notify_order_callbacks(self, order: Order, event: str):
        """Notificar callbacks de órdenes."""
        for callback in self.order_callbacks:
            try:
                await callback(order, event)
            except Exception as e:
                trading_logger.logger.error(f"❌ Error en callback de orden: {e}")
    
    async def _notify_fill_callbacks(self, fill: Fill):
        """Notificar callbacks de fills."""
        for callback in self.fill_callbacks:
            try:
                await callback(fill)
            except Exception as e:
                trading_logger.logger.error(f"❌ Error en callback de fill: {e}")
    
    async def _notify_position_callbacks(self, position: Position):
        """Notificar callbacks de posiciones."""
        for callback in self.position_callbacks:
            try:
                await callback(position)
            except Exception as e:
                trading_logger.logger.error(f"❌ Error en callback de posición: {e}")
    
    async def _load_state(self):
        """Cargar estado previo."""
        # TODO: Implementar carga desde base de datos
        pass
    
    async def _save_state(self):
        """Guardar estado actual."""
        # TODO: Implementar guardado en base de datos
        pass
    
    def add_order_callback(self, callback: Callable):
        """Agregar callback para eventos de órdenes."""
        self.order_callbacks.append(callback)
    
    def add_fill_callback(self, callback: Callable):
        """Agregar callback para fills."""
        self.fill_callbacks.append(callback)
    
    def add_position_callback(self, callback: Callable):
        """Agregar callback para posiciones."""
        self.position_callbacks.append(callback)
    
    async def stop(self):
        """Detener el gestor de órdenes."""
        trading_logger.logger.info("🛑 Deteniendo Order Manager...")
        
        # Cancelar órdenes abiertas
        open_orders = await self.get_open_orders()
        for order in open_orders:
            await self.cancel_order(order.id)
        
        # Guardar estado
        await self._save_state()
        
        self.is_running = False
        trading_logger.logger.info("✅ Order Manager detenido")