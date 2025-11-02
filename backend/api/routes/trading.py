"""
API endpoints para operaciones de trading
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.agents.agent_manager import AgentManager
from backend.services.websocket_manager import WebSocketManager

router = APIRouter()

# Modelos Pydantic para requests/responses
class TradeRequest(BaseModel):
    symbol: str
    side: str  # BUY o SELL
    quantity: float
    order_type: str = "MARKET"
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy: str = "manual"

class TradeResponse(BaseModel):
    success: bool
    trade_id: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = None

class PositionResponse(BaseModel):
    success: bool
    positions: Dict[str, Any]
    total_value: float
    unrealized_pnl: float

class PortfolioResponse(BaseModel):
    success: bool
    portfolio: Dict[str, Any]
    timestamp: str

# Dependencias
def get_agent_manager() -> AgentManager:
    """Obtener instancia del AgentManager"""
    # En producción, esto vendría del contexto de la aplicación
    from backend.main import get_agent_manager
    return get_agent_manager()

def get_websocket_manager() -> WebSocketManager:
    """Obtener instancia del WebSocketManager"""
    from backend.main import get_websocket_manager
    return get_websocket_manager()

@router.post("/execute", response_model=TradeResponse)
async def execute_trade(
    trade_request: TradeRequest,
    agent_manager: AgentManager = Depends(get_agent_manager),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Ejecutar una operación de trading
    """
    try:
        if not agent_manager or not agent_manager.is_running:
            raise HTTPException(status_code=503, detail="Sistema de agentes no disponible")
        
        # Ejecutar workflow de trading
        workflow_result = await agent_manager.execute_trading_workflow({
            "symbol": trade_request.symbol,
            "side": trade_request.side,
            "quantity": trade_request.quantity,
            "order_type": trade_request.order_type,
            "price": trade_request.price,
            "stop_loss": trade_request.stop_loss,
            "take_profit": trade_request.take_profit,
            "strategy": trade_request.strategy
        })
        
        # Enviar actualización por WebSocket
        if ws_manager:
            await ws_manager.send_trade_update({
                "workflow_id": workflow_result.get("workflow_id"),
                "status": workflow_result.get("status"),
                "symbol": trade_request.symbol,
                "side": trade_request.side,
                "quantity": trade_request.quantity
            })
        
        if workflow_result.get("status") == "completed":
            return TradeResponse(
                success=True,
                trade_id=workflow_result.get("final_result", {}).get("trade_id"),
                message="Trade ejecutado exitosamente",
                data=workflow_result
            )
        else:
            return TradeResponse(
                success=False,
                message=workflow_result.get("reason", "Error ejecutando trade"),
                data=workflow_result
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ejecutando trade: {str(e)}")

@router.get("/positions", response_model=PositionResponse)
async def get_positions(
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """
    Obtener posiciones activas
    """
    try:
        if not agent_manager or not agent_manager.is_running:
            raise HTTPException(status_code=503, detail="Sistema de agentes no disponible")
        
        # Obtener estado del portafolio
        portfolio_status = await agent_manager._get_current_portfolio_status()
        
        active_positions = portfolio_status.get("active_positions", {})
        total_unrealized_pnl = sum(
            pos.get("unrealized_pnl", 0) for pos in active_positions.values()
        )
        total_position_value = sum(
            pos.get("current_price", 0) * pos.get("quantity", 0) 
            for pos in active_positions.values()
            if pos.get("quantity", 0) > 0
        )
        
        return PositionResponse(
            success=True,
            positions=active_positions,
            total_value=total_position_value,
            unrealized_pnl=total_unrealized_pnl
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo posiciones: {str(e)}")

@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(
    agent_manager: AgentManager = Depends(get_agent_manager),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Obtener estado completo del portafolio
    """
    try:
        if not agent_manager or not agent_manager.is_running:
            raise HTTPException(status_code=503, detail="Sistema de agentes no disponible")
        
        # Obtener estado del portafolio
        portfolio_status = await agent_manager._get_current_portfolio_status()
        
        # Enviar actualización por WebSocket
        if ws_manager:
            await ws_manager.send_portfolio_update(portfolio_status)
        
        return PortfolioResponse(
            success=True,
            portfolio=portfolio_status,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo portafolio: {str(e)}")

@router.post("/close-position")
async def close_position(
    symbol: str,
    quantity: Optional[float] = None,
    agent_manager: AgentManager = Depends(get_agent_manager),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Cerrar una posición específica
    """
    try:
        if not agent_manager or not agent_manager.is_running:
            raise HTTPException(status_code=503, detail="Sistema de agentes no disponible")
        
        trading_agent = agent_manager.agents.get("trading")
        if not trading_agent:
            raise HTTPException(status_code=503, detail="Trading agent no disponible")
        
        # Crear tarea para cerrar posición
        from backend.agents.base_agent import AgentTask
        
        task = AgentTask(
            task_id=f"close_position_{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            task_type="close_position",
            parameters={
                "symbol": symbol,
                "quantity": quantity
            }
        )
        
        await trading_agent.add_task(task)
        
        # Enviar actualización por WebSocket
        if ws_manager:
            await ws_manager.send_trade_update({
                "action": "close_position",
                "symbol": symbol,
                "quantity": quantity,
                "task_id": task.task_id
            })
        
        return {
            "success": True,
            "message": f"Solicitud de cierre de posición enviada para {symbol}",
            "task_id": task.task_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cerrando posición: {str(e)}")

@router.post("/cancel-order")
async def cancel_order(
    symbol: str,
    order_id: str,
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """
    Cancelar una orden pendiente
    """
    try:
        if not agent_manager or not agent_manager.is_running:
            raise HTTPException(status_code=503, detail="Sistema de agentes no disponible")
        
        trading_agent = agent_manager.agents.get("trading")
        if not trading_agent:
            raise HTTPException(status_code=503, detail="Trading agent no disponible")
        
        # Crear tarea para cancelar orden
        from backend.agents.base_agent import AgentTask
        
        task = AgentTask(
            task_id=f"cancel_order_{order_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            task_type="cancel_order",
            parameters={
                "symbol": symbol,
                "order_id": order_id
            }
        )
        
        await trading_agent.add_task(task)
        
        return {
            "success": True,
            "message": f"Solicitud de cancelación enviada para orden {order_id}",
            "task_id": task.task_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelando orden: {str(e)}")

@router.get("/history")
async def get_trading_history(
    symbol: Optional[str] = None,
    limit: int = 100,
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """
    Obtener historial de trading
    """
    try:
        # En una implementación real, esto consultaría la base de datos
        # Por ahora retornamos datos simulados
        
        history = {
            "trades": [],
            "total_trades": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "filters": {
                "symbol": symbol,
                "limit": limit
            }
        }
        
        return {
            "success": True,
            "data": history,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")

@router.get("/performance")
async def get_trading_performance(
    period: str = "1d",  # 1d, 1w, 1m, 3m, 1y
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """
    Obtener métricas de performance de trading
    """
    try:
        # Obtener estado actual del portafolio
        portfolio_status = await agent_manager._get_current_portfolio_status()
        
        # Calcular métricas básicas
        performance = {
            "period": period,
            "total_return": 0.0,
            "total_return_pct": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "current_balance": portfolio_status.get("current_balance", 1000.0),
            "total_portfolio_value": portfolio_status.get("total_portfolio_value", 1000.0),
            "unrealized_pnl": portfolio_status.get("total_unrealized_pnl", 0.0)
        }
        
        return {
            "success": True,
            "performance": performance,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo performance: {str(e)}")

@router.get("/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100
):
    """
    Obtener datos de mercado para un símbolo
    """
    try:
        # En una implementación real, esto usaría el BinanceService
        # Por ahora retornamos datos simulados
        
        market_data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "current_price": 45000.0,  # Precio simulado
            "price_change_24h": 2.5,
            "volume_24h": 1000000.0,
            "high_24h": 46000.0,
            "low_24h": 44000.0,
            "data_points": limit,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "data": market_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos de mercado: {str(e)}")

@router.post("/update-stop-loss")
async def update_stop_loss(
    trade_id: str,
    stop_loss: float,
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """
    Actualizar stop-loss de un trade
    """
    try:
        if not agent_manager or not agent_manager.is_running:
            raise HTTPException(status_code=503, detail="Sistema de agentes no disponible")
        
        trading_agent = agent_manager.agents.get("trading")
        if not trading_agent:
            raise HTTPException(status_code=503, detail="Trading agent no disponible")
        
        # Crear tarea para actualizar stop-loss
        from backend.agents.base_agent import AgentTask
        
        task = AgentTask(
            task_id=f"update_sl_{trade_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            task_type="update_stop_loss",
            parameters={
                "trade_id": trade_id,
                "stop_loss": stop_loss
            }
        )
        
        await trading_agent.add_task(task)
        
        return {
            "success": True,
            "message": f"Stop-loss actualizado para trade {trade_id}",
            "task_id": task.task_id,
            "new_stop_loss": stop_loss
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando stop-loss: {str(e)}")

@router.post("/update-take-profit")
async def update_take_profit(
    trade_id: str,
    take_profit: float,
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """
    Actualizar take-profit de un trade
    """
    try:
        if not agent_manager or not agent_manager.is_running:
            raise HTTPException(status_code=503, detail="Sistema de agentes no disponible")
        
        trading_agent = agent_manager.agents.get("trading")
        if not trading_agent:
            raise HTTPException(status_code=503, detail="Trading agent no disponible")
        
        # Crear tarea para actualizar take-profit
        from backend.agents.base_agent import AgentTask
        
        task = AgentTask(
            task_id=f"update_tp_{trade_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            task_type="update_take_profit",
            parameters={
                "trade_id": trade_id,
                "take_profit": take_profit
            }
        )
        
        await trading_agent.add_task(task)
        
        return {
            "success": True,
            "message": f"Take-profit actualizado para trade {trade_id}",
            "task_id": task.task_id,
            "new_take_profit": take_profit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando take-profit: {str(e)}")

@router.get("/account-info")
async def get_account_info():
    """
    Obtener información de la cuenta de trading
    """
    try:
        # En una implementación real, esto usaría el BinanceService
        account_info = {
            "account_type": "TESTNET",
            "can_trade": True,
            "can_withdraw": False,
            "can_deposit": False,
            "balances": [
                {"asset": "USDT", "free": "1000.00000000", "locked": "0.00000000"},
                {"asset": "BTC", "free": "0.00000000", "locked": "0.00000000"},
                {"asset": "ETH", "free": "0.00000000", "locked": "0.00000000"}
            ],
            "permissions": ["SPOT"],
            "update_time": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "account_info": account_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo información de cuenta: {str(e)}")