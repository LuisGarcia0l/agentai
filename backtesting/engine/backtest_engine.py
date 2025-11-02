"""
🔬 Motor de Backtesting Avanzado

Sistema completo de backtesting para validar estrategias de trading
con métricas detalladas y análisis de rendimiento.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

from strategies.technical.indicators import TradingStrategy, TradingSignal, SignalType
from utils.logging.logger import trading_logger


class OrderType(Enum):
    """Tipos de órdenes."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Estados de órdenes."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Orden de trading."""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    timestamp: Optional[datetime] = None
    filled_price: Optional[float] = None
    filled_quantity: float = 0.0
    commission: float = 0.0


@dataclass
class Position:
    """Posición de trading."""
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    @property
    def market_value(self) -> float:
        """Valor de mercado de la posición."""
        return self.quantity * self.avg_price
    
    @property
    def is_long(self) -> bool:
        """Verificar si es posición larga."""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Verificar si es posición corta."""
        return self.quantity < 0
    
    @property
    def is_flat(self) -> bool:
        """Verificar si no hay posición."""
        return abs(self.quantity) < 1e-8


@dataclass
class Trade:
    """Trade completado."""
    id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_percent: float
    commission: float
    duration: timedelta
    
    @property
    def is_winner(self) -> bool:
        """Verificar si es trade ganador."""
        return self.pnl > 0


@dataclass
class Portfolio:
    """Estado del portafolio."""
    initial_capital: float
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    orders: List[Order] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)
    
    @property
    def total_value(self) -> float:
        """Valor total del portafolio."""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value
    
    @property
    def total_pnl(self) -> float:
        """PnL total."""
        return self.total_value - self.initial_capital
    
    @property
    def total_pnl_percent(self) -> float:
        """PnL total en porcentaje."""
        return (self.total_pnl / self.initial_capital) * 100


class BacktestEngine:
    """Motor principal de backtesting."""
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001,  # 0.1%
        slippage: float = 0.0001,  # 0.01%
        max_position_size: float = 0.95  # 95% del capital
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.max_position_size = max_position_size
        
        self.portfolio = Portfolio(
            initial_capital=initial_capital,
            cash=initial_capital
        )
        
        self.current_time: Optional[datetime] = None
        self.current_prices: Dict[str, float] = {}
        
    def run_backtest(
        self,
        strategy: TradingStrategy,
        data: pd.DataFrame,
        symbol: str = "BTCUSDT"
    ) -> Dict[str, Any]:
        """
        Ejecutar backtesting completo.
        
        Args:
            strategy: Estrategia de trading
            data: DataFrame con datos OHLCV
            symbol: Símbolo del activo
        
        Returns:
            Resultados del backtesting
        """
        trading_logger.logger.info(f"🔬 Iniciando backtesting de {strategy.name}")
        trading_logger.logger.info(f"📊 Datos: {len(data)} velas, período: {data.index[0]} - {data.index[-1]}")
        
        # Resetear portafolio
        self._reset_portfolio()
        
        # Procesar cada vela
        for timestamp, row in data.iterrows():
            self.current_time = timestamp
            self.current_prices[symbol] = row['close']
            
            # Actualizar posiciones
            self._update_positions()
            
            # Procesar órdenes pendientes
            self._process_pending_orders(row)
            
            # Obtener señal de la estrategia
            # Crear ventana de datos hasta el momento actual
            current_idx = data.index.get_loc(timestamp)
            window_data = data.iloc[:current_idx + 1]
            
            if len(window_data) >= 50:  # Mínimo de datos para análisis
                signal = strategy.analyze(window_data)
                
                if signal and signal.signal != SignalType.HOLD:
                    self._process_signal(signal, symbol, row)
            
            # Guardar estado del portafolio
            self.portfolio.equity_curve.append((timestamp, self.portfolio.total_value))
        
        # Cerrar posiciones abiertas al final
        self._close_all_positions()
        
        # Calcular métricas
        results = self._calculate_metrics()
        
        trading_logger.logger.info(f"✅ Backtesting completado")
        trading_logger.logger.info(f"📈 Rendimiento total: {results['total_return']:.2f}%")
        trading_logger.logger.info(f"🎯 Trades ganadores: {results['win_rate']:.1f}%")
        
        return results
    
    def _reset_portfolio(self):
        """Resetear el portafolio."""
        self.portfolio = Portfolio(
            initial_capital=self.initial_capital,
            cash=self.initial_capital
        )
    
    def _update_positions(self):
        """Actualizar el valor de las posiciones."""
        for symbol, position in self.portfolio.positions.items():
            if not position.is_flat and symbol in self.current_prices:
                current_price = self.current_prices[symbol]
                position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
    
    def _process_pending_orders(self, market_data: pd.Series):
        """Procesar órdenes pendientes."""
        filled_orders = []
        
        for order in self.portfolio.orders:
            if order.status != OrderStatus.PENDING:
                continue
            
            # Simular ejecución de orden
            if self._should_fill_order(order, market_data):
                self._fill_order(order, market_data)
                filled_orders.append(order)
        
        # Remover órdenes ejecutadas
        self.portfolio.orders = [
            order for order in self.portfolio.orders 
            if order not in filled_orders
        ]
    
    def _should_fill_order(self, order: Order, market_data: pd.Series) -> bool:
        """Determinar si una orden debe ejecutarse."""
        if order.type == OrderType.MARKET:
            return True
        
        elif order.type == OrderType.LIMIT:
            if order.side == 'buy':
                return market_data['low'] <= order.price
            else:
                return market_data['high'] >= order.price
        
        elif order.type == OrderType.STOP:
            if order.side == 'buy':
                return market_data['high'] >= order.stop_price
            else:
                return market_data['low'] <= order.stop_price
        
        return False
    
    def _fill_order(self, order: Order, market_data: pd.Series):
        """Ejecutar una orden."""
        # Determinar precio de ejecución
        if order.type == OrderType.MARKET:
            fill_price = market_data['close']
        elif order.type == OrderType.LIMIT:
            fill_price = order.price
        else:
            fill_price = order.stop_price
        
        # Aplicar slippage
        if order.side == 'buy':
            fill_price *= (1 + self.slippage)
        else:
            fill_price *= (1 - self.slippage)
        
        # Calcular comisión
        commission = order.quantity * fill_price * self.commission_rate
        
        # Actualizar orden
        order.status = OrderStatus.FILLED
        order.filled_price = fill_price
        order.filled_quantity = order.quantity
        order.commission = commission
        order.timestamp = self.current_time
        
        # Actualizar posición
        self._update_position(order)
        
        # Actualizar cash
        if order.side == 'buy':
            self.portfolio.cash -= (order.quantity * fill_price + commission)
        else:
            self.portfolio.cash += (order.quantity * fill_price - commission)
    
    def _update_position(self, order: Order):
        """Actualizar posición después de ejecutar orden."""
        symbol = order.symbol
        
        if symbol not in self.portfolio.positions:
            self.portfolio.positions[symbol] = Position(symbol=symbol)
        
        position = self.portfolio.positions[symbol]
        
        if order.side == 'buy':
            # Compra
            if position.quantity >= 0:
                # Aumentar posición larga
                total_cost = (position.quantity * position.avg_price + 
                             order.filled_quantity * order.filled_price)
                position.quantity += order.filled_quantity
                position.avg_price = total_cost / position.quantity if position.quantity > 0 else 0
            else:
                # Reducir posición corta
                if order.filled_quantity >= abs(position.quantity):
                    # Cerrar posición corta y abrir larga
                    remaining = order.filled_quantity - abs(position.quantity)
                    self._close_position(position, order.filled_price)
                    if remaining > 0:
                        position.quantity = remaining
                        position.avg_price = order.filled_price
                else:
                    # Solo reducir posición corta
                    position.quantity += order.filled_quantity
        
        else:  # sell
            # Venta
            if position.quantity <= 0:
                # Aumentar posición corta
                total_cost = (abs(position.quantity) * position.avg_price + 
                             order.filled_quantity * order.filled_price)
                position.quantity -= order.filled_quantity
                position.avg_price = total_cost / abs(position.quantity) if position.quantity < 0 else 0
            else:
                # Reducir posición larga
                if order.filled_quantity >= position.quantity:
                    # Cerrar posición larga y abrir corta
                    remaining = order.filled_quantity - position.quantity
                    self._close_position(position, order.filled_price)
                    if remaining > 0:
                        position.quantity = -remaining
                        position.avg_price = order.filled_price
                else:
                    # Solo reducir posición larga
                    position.quantity -= order.filled_quantity
    
    def _close_position(self, position: Position, exit_price: float):
        """Cerrar una posición y registrar el trade."""
        if position.is_flat:
            return
        
        # Calcular PnL
        if position.is_long:
            pnl = (exit_price - position.avg_price) * position.quantity
        else:
            pnl = (position.avg_price - exit_price) * abs(position.quantity)
        
        pnl_percent = (pnl / (position.avg_price * abs(position.quantity))) * 100
        
        # Crear trade
        trade = Trade(
            id=f"trade_{len(self.portfolio.trades) + 1}",
            symbol=position.symbol,
            side="long" if position.is_long else "short",
            entry_price=position.avg_price,
            exit_price=exit_price,
            quantity=abs(position.quantity),
            entry_time=self.current_time,  # Simplificado
            exit_time=self.current_time,
            pnl=pnl,
            pnl_percent=pnl_percent,
            commission=0.0,  # Simplificado
            duration=timedelta(0)  # Simplificado
        )
        
        self.portfolio.trades.append(trade)
        position.realized_pnl += pnl
        position.quantity = 0.0
        position.avg_price = 0.0
        position.unrealized_pnl = 0.0
    
    def _process_signal(self, signal: TradingSignal, symbol: str, market_data: pd.Series):
        """Procesar señal de trading."""
        # Calcular tamaño de posición
        position_size = self._calculate_position_size(signal, symbol)
        
        if position_size == 0:
            return
        
        # Crear orden
        if signal.signal == SignalType.BUY:
            order = Order(
                id=f"order_{len(self.portfolio.orders) + 1}",
                symbol=symbol,
                side='buy',
                type=OrderType.MARKET,
                quantity=position_size
            )
        else:  # SELL
            order = Order(
                id=f"order_{len(self.portfolio.orders) + 1}",
                symbol=symbol,
                side='sell',
                type=OrderType.MARKET,
                quantity=position_size
            )
        
        self.portfolio.orders.append(order)
        
        trading_logger.trade_signal(
            symbol=symbol,
            action=signal.signal.value,
            price=signal.price,
            reason=signal.reason
        )
    
    def _calculate_position_size(self, signal: TradingSignal, symbol: str) -> float:
        """Calcular tamaño de posición."""
        current_price = self.current_prices.get(symbol, signal.price)
        max_position_value = self.portfolio.total_value * self.max_position_size
        
        # Tamaño basado en fuerza de la señal
        base_size = (max_position_value * signal.strength) / current_price
        
        # Verificar disponibilidad de cash
        if signal.signal == SignalType.BUY:
            max_affordable = self.portfolio.cash / current_price
            return min(base_size, max_affordable * 0.95)  # 95% del cash disponible
        else:
            # Para ventas, verificar posición actual
            current_position = self.portfolio.positions.get(symbol)
            if current_position and current_position.quantity > 0:
                return min(base_size, current_position.quantity)
            else:
                # Venta en corto (si está permitida)
                return base_size
    
    def _close_all_positions(self):
        """Cerrar todas las posiciones abiertas."""
        for symbol, position in self.portfolio.positions.items():
            if not position.is_flat and symbol in self.current_prices:
                exit_price = self.current_prices[symbol]
                self._close_position(position, exit_price)
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calcular métricas de rendimiento."""
        trades = self.portfolio.trades
        equity_curve = pd.DataFrame(self.portfolio.equity_curve, columns=['timestamp', 'equity'])
        equity_curve.set_index('timestamp', inplace=True)
        
        if len(trades) == 0:
            return {
                'total_return': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'calmar_ratio': 0.0,
                'equity_curve': equity_curve
            }
        
        # Métricas básicas
        total_return = self.portfolio.total_pnl_percent
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.is_winner]
        losing_trades = [t for t in trades if not t.is_winner]
        
        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Drawdown
        equity_curve['peak'] = equity_curve['equity'].cummax()
        equity_curve['drawdown'] = (equity_curve['equity'] - equity_curve['peak']) / equity_curve['peak']
        max_drawdown = abs(equity_curve['drawdown'].min()) * 100
        
        # Sharpe Ratio
        if len(equity_curve) > 1:
            returns = equity_curve['equity'].pct_change().dropna()
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calmar Ratio
        annual_return = total_return  # Simplificado
        calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
        
        return {
            'total_return': total_return,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'calmar_ratio': calmar_ratio,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'final_capital': self.portfolio.total_value,
            'equity_curve': equity_curve,
            'trades': trades
        }