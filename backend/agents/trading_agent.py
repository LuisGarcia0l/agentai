"""
Trading Agent - Agente especializado en ejecución de operaciones de trading
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal, ROUND_DOWN
import uuid

from backend.agents.base_agent import BaseAgent, AgentTask
from backend.services.binance_service import BinanceService
from backend.services.risk_manager import RiskManager
from backend.core.database import DatabaseManager
from backend.core.config import settings

class TradingAgent(BaseAgent):
    """
    Agente especializado en ejecución de operaciones de trading
    
    Responsabilidades:
    - Ejecutar órdenes de compra y venta
    - Gestionar posiciones abiertas
    - Implementar stop-loss y take-profit
    - Monitorear ejecución de órdenes
    - Reportar resultados de trading
    """
    
    def __init__(self):
        super().__init__(
            name="TradingAgent",
            description="Agente especializado en ejecución de operaciones de trading"
        )
        self.binance_service: Optional[BinanceService] = None
        self.risk_manager: Optional[RiskManager] = None
        self.active_positions = {}
        self.pending_orders = {}
        self.trading_session_id = None
        
    async def _initialize_agent(self):
        """Inicializar servicios del agente de trading"""
        # Inicializar servicio de Binance
        self.binance_service = BinanceService()
        await self.binance_service.initialize()
        
        # Inicializar gestor de riesgo
        self.risk_manager = RiskManager()
        await self.risk_manager.initialize()
        
        # Crear sesión de trading
        await self._create_trading_session()
        
        self.logger.info("TradingAgent inicializado con servicios de Binance y gestión de riesgo")
    
    async def _create_trading_session(self):
        """Crear nueva sesión de trading"""
        try:
            session_data = {
                "session_id": f"trading_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "start_time": datetime.utcnow(),
                "status": "active",
                "initial_balance": 1000.0,  # Balance inicial en testnet
                "current_balance": 1000.0,
                "active_strategies": [],
                "config": {
                    "max_position_size": settings.MAX_POSITION_SIZE,
                    "default_stop_loss": settings.DEFAULT_STOP_LOSS,
                    "default_take_profit": settings.DEFAULT_TAKE_PROFIT
                }
            }
            
            session = await DatabaseManager.create_trading_session(session_data)
            self.trading_session_id = session.session_id
            
            self.logger.info(f"Sesión de trading creada: {self.trading_session_id}")
            
        except Exception as e:
            self.logger.error(f"Error creando sesión de trading: {e}")
            raise
    
    async def _process_task(self, task: AgentTask) -> Any:
        """Procesar tareas de trading"""
        task_type = task.task_type
        parameters = task.parameters
        
        if task_type == "execute_trade":
            return await self._execute_trade(parameters)
        elif task_type == "close_position":
            return await self._close_position(parameters)
        elif task_type == "update_stop_loss":
            return await self._update_stop_loss(parameters)
        elif task_type == "update_take_profit":
            return await self._update_take_profit(parameters)
        elif task_type == "check_positions":
            return await self._check_positions(parameters)
        elif task_type == "cancel_order":
            return await self._cancel_order(parameters)
        elif task_type == "get_portfolio_status":
            return await self._get_portfolio_status(parameters)
        else:
            raise ValueError(f"Tipo de tarea no soportado: {task_type}")
    
    async def _execute_trade(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutar una operación de trading
        
        Args:
            parameters: Debe contener 'symbol', 'side', 'quantity', 'strategy', etc.
            
        Returns:
            Resultado de la ejecución
        """
        symbol = parameters.get("symbol")
        side = parameters.get("side")  # BUY o SELL
        quantity = parameters.get("quantity")
        order_type = parameters.get("order_type", "MARKET")
        price = parameters.get("price")
        strategy = parameters.get("strategy", "manual")
        stop_loss = parameters.get("stop_loss")
        take_profit = parameters.get("take_profit")
        
        if not all([symbol, side, quantity]):
            raise ValueError("Parámetros requeridos: symbol, side, quantity")
        
        self.logger.info(f"Ejecutando trade: {side} {quantity} {symbol}")
        
        try:
            # Verificar riesgo antes de ejecutar
            risk_check = await self.risk_manager.check_trade_risk({
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "current_balance": await self._get_current_balance(),
                "active_positions": self.active_positions
            })
            
            if not risk_check["approved"]:
                return {
                    "success": False,
                    "error": f"Trade rechazado por gestión de riesgo: {risk_check['reason']}",
                    "risk_check": risk_check
                }
            
            # Ejecutar orden en Binance
            order_result = await self.binance_service.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price
            )
            
            if not order_result["success"]:
                return {
                    "success": False,
                    "error": f"Error ejecutando orden: {order_result.get('error', 'Unknown error')}",
                    "order_result": order_result
                }
            
            # Generar ID único para el trade
            trade_id = f"trade_{uuid.uuid4().hex[:8]}"
            
            # Registrar trade en base de datos
            trade_data = {
                "session_id": self.trading_session_id,
                "trade_id": trade_id,
                "symbol": symbol,
                "side": side,
                "order_type": order_type,
                "quantity": float(quantity),
                "price": float(price) if price else None,
                "executed_price": float(order_result.get("executed_price", 0)),
                "executed_quantity": float(order_result.get("executed_quantity", 0)),
                "status": order_result.get("status", "UNKNOWN"),
                "strategy": strategy,
                "agent": self.name,
                "stop_loss": float(stop_loss) if stop_loss else None,
                "take_profit": float(take_profit) if take_profit else None,
                "metadata": {
                    "binance_order_id": order_result.get("order_id"),
                    "risk_check": risk_check,
                    "parameters": parameters
                }
            }
            
            trade_record = await DatabaseManager.record_trade(trade_data)
            
            # Actualizar posiciones activas
            if order_result.get("status") == "FILLED":
                await self._update_active_positions(trade_record, order_result)
                
                # Configurar stop-loss y take-profit si se especificaron
                if stop_loss or take_profit:
                    await self._setup_exit_orders(trade_record, stop_loss, take_profit)
            
            result = {
                "success": True,
                "trade_id": trade_id,
                "order_result": order_result,
                "trade_record": {
                    "id": trade_record.id,
                    "symbol": trade_record.symbol,
                    "side": trade_record.side,
                    "quantity": trade_record.quantity,
                    "executed_price": trade_record.executed_price,
                    "status": trade_record.status
                },
                "risk_check": risk_check
            }
            
            self.logger.info(f"Trade ejecutado exitosamente: {trade_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error ejecutando trade: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_active_positions(self, trade_record, order_result: Dict[str, Any]):
        """Actualizar posiciones activas"""
        symbol = trade_record.symbol
        side = trade_record.side
        quantity = float(order_result.get("executed_quantity", 0))
        price = float(order_result.get("executed_price", 0))
        
        if symbol not in self.active_positions:
            self.active_positions[symbol] = {
                "quantity": 0.0,
                "average_price": 0.0,
                "total_cost": 0.0,
                "unrealized_pnl": 0.0,
                "trades": []
            }
        
        position = self.active_positions[symbol]
        
        if side == "BUY":
            # Aumentar posición
            new_total_cost = position["total_cost"] + (quantity * price)
            new_quantity = position["quantity"] + quantity
            position["average_price"] = new_total_cost / new_quantity if new_quantity > 0 else 0
            position["quantity"] = new_quantity
            position["total_cost"] = new_total_cost
        else:  # SELL
            # Reducir posición
            position["quantity"] -= quantity
            if position["quantity"] <= 0:
                # Posición cerrada
                position["quantity"] = 0
                position["average_price"] = 0
                position["total_cost"] = 0
        
        position["trades"].append({
            "trade_id": trade_record.trade_id,
            "side": side,
            "quantity": quantity,
            "price": price,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        self.logger.debug(f"Posición actualizada para {symbol}: {position}")
    
    async def _setup_exit_orders(self, trade_record, stop_loss: float = None, take_profit: float = None):
        """Configurar órdenes de salida (stop-loss y take-profit)"""
        try:
            symbol = trade_record.symbol
            side = trade_record.side
            quantity = trade_record.executed_quantity
            
            # Determinar lado opuesto para órdenes de salida
            exit_side = "SELL" if side == "BUY" else "BUY"
            
            # Configurar stop-loss
            if stop_loss:
                stop_order = await self.binance_service.place_order(
                    symbol=symbol,
                    side=exit_side,
                    order_type="STOP_LOSS_LIMIT",
                    quantity=quantity,
                    price=stop_loss,
                    stop_price=stop_loss
                )
                
                if stop_order["success"]:
                    self.pending_orders[f"{trade_record.trade_id}_stop_loss"] = {
                        "order_id": stop_order.get("order_id"),
                        "type": "stop_loss",
                        "trade_id": trade_record.trade_id,
                        "symbol": symbol,
                        "price": stop_loss
                    }
                    self.logger.info(f"Stop-loss configurado para {trade_record.trade_id} en {stop_loss}")
            
            # Configurar take-profit
            if take_profit:
                tp_order = await self.binance_service.place_order(
                    symbol=symbol,
                    side=exit_side,
                    order_type="LIMIT",
                    quantity=quantity,
                    price=take_profit
                )
                
                if tp_order["success"]:
                    self.pending_orders[f"{trade_record.trade_id}_take_profit"] = {
                        "order_id": tp_order.get("order_id"),
                        "type": "take_profit",
                        "trade_id": trade_record.trade_id,
                        "symbol": symbol,
                        "price": take_profit
                    }
                    self.logger.info(f"Take-profit configurado para {trade_record.trade_id} en {take_profit}")
                    
        except Exception as e:
            self.logger.error(f"Error configurando órdenes de salida: {e}")
    
    async def _close_position(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Cerrar una posición específica"""
        symbol = parameters.get("symbol")
        quantity = parameters.get("quantity")  # Si no se especifica, cerrar toda la posición
        
        if not symbol:
            raise ValueError("Se requiere especificar el símbolo")
        
        if symbol not in self.active_positions or self.active_positions[symbol]["quantity"] <= 0:
            return {
                "success": False,
                "error": f"No hay posición activa para {symbol}"
            }
        
        position = self.active_positions[symbol]
        close_quantity = quantity if quantity else position["quantity"]
        
        # Determinar lado de cierre
        close_side = "SELL"  # Asumiendo posiciones largas por simplicidad
        
        try:
            # Ejecutar orden de cierre
            result = await self._execute_trade({
                "symbol": symbol,
                "side": close_side,
                "quantity": close_quantity,
                "order_type": "MARKET",
                "strategy": "position_close"
            })
            
            if result["success"]:
                self.logger.info(f"Posición cerrada para {symbol}: {close_quantity}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error cerrando posición: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _check_positions(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar y actualizar estado de posiciones"""
        try:
            # Obtener precios actuales para calcular PnL
            updated_positions = {}
            
            for symbol, position in self.active_positions.items():
                if position["quantity"] > 0:
                    # Obtener precio actual
                    current_price = await self.binance_service.get_current_price(symbol)
                    
                    if current_price:
                        # Calcular PnL no realizado
                        unrealized_pnl = (current_price - position["average_price"]) * position["quantity"]
                        position["unrealized_pnl"] = unrealized_pnl
                        position["current_price"] = current_price
                        position["pnl_percentage"] = (unrealized_pnl / position["total_cost"]) * 100 if position["total_cost"] > 0 else 0
                        
                        updated_positions[symbol] = position
            
            self.active_positions = updated_positions
            
            return {
                "success": True,
                "positions": self.active_positions,
                "total_unrealized_pnl": sum(pos["unrealized_pnl"] for pos in self.active_positions.values()),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error verificando posiciones: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_portfolio_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener estado completo del portafolio"""
        try:
            # Actualizar posiciones
            positions_result = await self._check_positions({})
            
            # Obtener balance actual
            current_balance = await self._get_current_balance()
            
            # Calcular métricas del portafolio
            total_unrealized_pnl = sum(pos["unrealized_pnl"] for pos in self.active_positions.values())
            total_position_value = sum(pos["current_price"] * pos["quantity"] for pos in self.active_positions.values() if "current_price" in pos)
            
            portfolio_status = {
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": self.trading_session_id,
                "current_balance": current_balance,
                "total_position_value": total_position_value,
                "total_unrealized_pnl": total_unrealized_pnl,
                "total_portfolio_value": current_balance + total_position_value,
                "active_positions": self.active_positions,
                "pending_orders": len(self.pending_orders),
                "performance": {
                    "total_return": total_unrealized_pnl,
                    "return_percentage": (total_unrealized_pnl / 1000.0) * 100,  # Asumiendo balance inicial de 1000
                    "active_positions_count": len([pos for pos in self.active_positions.values() if pos["quantity"] > 0])
                }
            }
            
            return {
                "success": True,
                "portfolio": portfolio_status
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del portafolio: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_current_balance(self) -> float:
        """Obtener balance actual de la cuenta"""
        try:
            account_info = await self.binance_service.get_account_info()
            if account_info and "balances" in account_info:
                # Buscar balance de USDT
                for balance in account_info["balances"]:
                    if balance["asset"] == "USDT":
                        return float(balance["free"]) + float(balance["locked"])
            return 1000.0  # Balance por defecto para testnet
        except Exception as e:
            self.logger.error(f"Error obteniendo balance: {e}")
            return 1000.0
    
    async def _update_stop_loss(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar stop-loss de una posición"""
        trade_id = parameters.get("trade_id")
        new_stop_loss = parameters.get("stop_loss")
        
        if not all([trade_id, new_stop_loss]):
            raise ValueError("Se requieren trade_id y stop_loss")
        
        try:
            # Buscar orden de stop-loss existente
            stop_loss_key = f"{trade_id}_stop_loss"
            
            if stop_loss_key in self.pending_orders:
                # Cancelar orden existente
                old_order = self.pending_orders[stop_loss_key]
                cancel_result = await self.binance_service.cancel_order(
                    old_order["symbol"], 
                    old_order["order_id"]
                )
                
                if cancel_result["success"]:
                    del self.pending_orders[stop_loss_key]
            
            # Crear nueva orden de stop-loss
            # (Implementación simplificada - en producción necesitaría más detalles)
            
            return {
                "success": True,
                "message": f"Stop-loss actualizado para {trade_id}",
                "new_stop_loss": new_stop_loss
            }
            
        except Exception as e:
            self.logger.error(f"Error actualizando stop-loss: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_take_profit(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar take-profit de una posición"""
        trade_id = parameters.get("trade_id")
        new_take_profit = parameters.get("take_profit")
        
        if not all([trade_id, new_take_profit]):
            raise ValueError("Se requieren trade_id y take_profit")
        
        try:
            # Similar a update_stop_loss pero para take-profit
            tp_key = f"{trade_id}_take_profit"
            
            if tp_key in self.pending_orders:
                old_order = self.pending_orders[tp_key]
                cancel_result = await self.binance_service.cancel_order(
                    old_order["symbol"], 
                    old_order["order_id"]
                )
                
                if cancel_result["success"]:
                    del self.pending_orders[tp_key]
            
            return {
                "success": True,
                "message": f"Take-profit actualizado para {trade_id}",
                "new_take_profit": new_take_profit
            }
            
        except Exception as e:
            self.logger.error(f"Error actualizando take-profit: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _cancel_order(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Cancelar una orden pendiente"""
        symbol = parameters.get("symbol")
        order_id = parameters.get("order_id")
        
        if not all([symbol, order_id]):
            raise ValueError("Se requieren symbol y order_id")
        
        try:
            result = await self.binance_service.cancel_order(symbol, order_id)
            
            # Remover de órdenes pendientes si existe
            keys_to_remove = []
            for key, order_info in self.pending_orders.items():
                if order_info["order_id"] == order_id:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.pending_orders[key]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error cancelando orden: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _periodic_tasks(self):
        """Tareas periódicas del agente de trading"""
        # Verificar posiciones cada minuto
        if len(self.active_positions) > 0:
            await self._check_positions({})
        
        # Verificar órdenes pendientes
        if len(self.pending_orders) > 0:
            await self._check_pending_orders()
        
        await asyncio.sleep(0.1)
    
    async def _check_pending_orders(self):
        """Verificar estado de órdenes pendientes"""
        try:
            orders_to_remove = []
            
            for key, order_info in self.pending_orders.items():
                # Verificar estado de la orden
                order_status = await self.binance_service.get_order_status(
                    order_info["symbol"], 
                    order_info["order_id"]
                )
                
                if order_status and order_status.get("status") in ["FILLED", "CANCELED", "REJECTED"]:
                    orders_to_remove.append(key)
                    
                    if order_status.get("status") == "FILLED":
                        self.logger.info(f"Orden {order_info['type']} ejecutada: {key}")
            
            # Remover órdenes completadas
            for key in orders_to_remove:
                del self.pending_orders[key]
                
        except Exception as e:
            self.logger.error(f"Error verificando órdenes pendientes: {e}")