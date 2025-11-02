"""
🚀 FastAPI Backend para AI Trading System

API REST completa para el frontend React con endpoints para:
- Datos de mercado en tiempo real
- Gestión de agentes IA
- Backtesting y optimización
- Configuración del sistema
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
from datetime import datetime, timedelta
import uvicorn

from data.feeds.market_data import MarketDataManager
from agents.trading_agent.agent import TradingAgent
from agents.research_agent.agent import ResearchAgent
from agents.optimizer_agent.agent import OptimizerAgent
from strategies.technical.indicators import RSIStrategy, MACDStrategy, MultiIndicatorStrategy
from backtesting.engine.backtest_engine import BacktestEngine
from utils.config.settings import settings
from utils.logging.logger import trading_logger, setup_logging


# Modelos Pydantic para requests/responses
class TradingSignalResponse(BaseModel):
    signal: str
    strength: float
    price: float
    timestamp: str
    reason: str
    indicators: Dict[str, float]


class BacktestRequest(BaseModel):
    strategy_name: str
    parameters: Dict[str, Any]
    start_date: str
    end_date: str
    initial_capital: float = 10000


class BacktestResponse(BaseModel):
    total_return: float
    total_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    final_capital: float


class AgentStatusResponse(BaseModel):
    agent_id: str
    is_running: bool
    last_update: Optional[str]
    performance_metrics: Dict[str, Any]


class MarketDataResponse(BaseModel):
    symbol: str
    price: float
    change_24h: float
    volume: float
    timestamp: str


class OptimizationRequest(BaseModel):
    strategy_name: str
    base_parameters: Dict[str, Any]
    optimization_method: str = "genetic_algorithm"


# Inicializar FastAPI
app = FastAPI(
    title="AI Trading System API",
    description="API REST para sistema de trading con agentes IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales para componentes del sistema
market_data_manager: Optional[MarketDataManager] = None
trading_agent: Optional[TradingAgent] = None
research_agent: Optional[ResearchAgent] = None
optimizer_agent: Optional[OptimizerAgent] = None
backtest_engine: Optional[BacktestEngine] = None

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection closed, remove it
                self.active_connections.remove(connection)

manager = ConnectionManager()


@app.on_event("startup")
async def startup_event():
    """Inicializar componentes del sistema al arrancar."""
    global market_data_manager, trading_agent, research_agent, optimizer_agent, backtest_engine
    
    # Configurar logging
    setup_logging(level=settings.LOG_LEVEL)
    trading_logger.logger.info("🚀 Iniciando AI Trading System API")
    
    try:
        # Inicializar componentes
        market_data_manager = MarketDataManager()
        await market_data_manager.initialize()
        
        # Inicializar agentes
        trading_agent = TradingAgent(market_data_manager, settings)
        research_agent = ResearchAgent(market_data_manager, settings)
        optimizer_agent = OptimizerAgent(market_data_manager, settings)
        
        await trading_agent.initialize()
        await research_agent.initialize()
        await optimizer_agent.initialize()
        
        # Inicializar motor de backtesting
        backtest_engine = BacktestEngine(
            initial_capital=settings.BACKTEST_INITIAL_CAPITAL,
            commission_rate=0.001
        )
        
        trading_logger.logger.info("✅ API inicializada correctamente")
        
    except Exception as e:
        trading_logger.logger.error(f"❌ Error inicializando API: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Limpiar recursos al cerrar."""
    trading_logger.logger.info("🛑 Cerrando AI Trading System API")
    
    if trading_agent:
        await trading_agent.stop()
    if research_agent:
        await research_agent.stop()
    if optimizer_agent:
        await optimizer_agent.stop()
    if market_data_manager:
        await market_data_manager.close()


# ============================================================================
# ENDPOINTS DE DATOS DE MERCADO
# ============================================================================

@app.get("/api/market/ticker/{symbol}", response_model=MarketDataResponse)
async def get_ticker(symbol: str):
    """Obtener ticker actual de un símbolo."""
    try:
        ticker = await market_data_manager.get_ticker(symbol)
        if not ticker:
            raise HTTPException(status_code=404, detail="Símbolo no encontrado")
        
        return MarketDataResponse(
            symbol=ticker.symbol,
            price=ticker.price,
            change_24h=ticker.change_24h,
            volume=ticker.volume,
            timestamp=ticker.timestamp.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/ohlcv/{symbol}")
async def get_ohlcv(symbol: str, timeframe: str = "1h", limit: int = 100):
    """Obtener datos OHLCV."""
    try:
        ohlcv_data = await market_data_manager.get_ohlcv(symbol, timeframe, limit)
        
        if not ohlcv_data:
            raise HTTPException(status_code=404, detail="No hay datos disponibles")
        
        # Convertir a formato JSON
        data = []
        for candle in ohlcv_data:
            data.append({
                "timestamp": candle.timestamp.isoformat(),
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume
            })
        
        return {"symbol": symbol, "timeframe": timeframe, "data": data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/symbols")
async def get_available_symbols():
    """Obtener símbolos disponibles."""
    return {
        "symbols": [
            "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", 
            "LINKUSDT", "LTCUSDT", "XRPUSDT", "SOLUSDT"
        ]
    }


# ============================================================================
# ENDPOINTS DE AGENTES IA
# ============================================================================

@app.get("/api/agents/status", response_model=Dict[str, AgentStatusResponse])
async def get_agents_status():
    """Obtener estado de todos los agentes."""
    try:
        agents_status = {}
        
        if trading_agent:
            status = trading_agent.get_status()
            agents_status["trading_agent"] = AgentStatusResponse(
                agent_id=status["agent_id"],
                is_running=status["is_running"],
                last_update=status["last_update"],
                performance_metrics=status["performance_metrics"]
            )
        
        if research_agent:
            summary = await research_agent.get_research_summary()
            agents_status["research_agent"] = AgentStatusResponse(
                agent_id=research_agent.agent_id,
                is_running=research_agent.is_running,
                last_update=summary.get("last_research"),
                performance_metrics=summary
            )
        
        if optimizer_agent:
            summary = await optimizer_agent.get_optimization_summary()
            agents_status["optimizer_agent"] = AgentStatusResponse(
                agent_id=optimizer_agent.agent_id,
                is_running=optimizer_agent.is_running,
                last_update=None,
                performance_metrics=summary
            )
        
        return agents_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/trading/start")
async def start_trading_agent():
    """Iniciar el agente de trading."""
    try:
        if not trading_agent.state.is_running:
            # Iniciar en background task
            asyncio.create_task(trading_agent.run())
            return {"message": "Trading agent iniciado", "status": "running"}
        else:
            return {"message": "Trading agent ya está ejecutándose", "status": "running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/trading/stop")
async def stop_trading_agent():
    """Detener el agente de trading."""
    try:
        await trading_agent.stop()
        return {"message": "Trading agent detenido", "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/trading/decisions")
async def get_trading_decisions(limit: int = 50):
    """Obtener historial de decisiones del trading agent."""
    try:
        if not trading_agent:
            raise HTTPException(status_code=404, detail="Trading agent no disponible")
        
        decisions = trading_agent.decision_history[-limit:]
        
        return {
            "decisions": [
                {
                    "timestamp": d.timestamp.isoformat(),
                    "symbol": d.symbol,
                    "action": d.action,
                    "confidence": d.confidence,
                    "quantity": d.quantity,
                    "reasoning": d.reasoning,
                    "risk_assessment": d.risk_assessment
                }
                for d in decisions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE ESTRATEGIAS Y SEÑALES
# ============================================================================

@app.get("/api/strategies/available")
async def get_available_strategies():
    """Obtener estrategias disponibles."""
    return {
        "strategies": [
            {
                "name": "RSI",
                "description": "Relative Strength Index Strategy",
                "parameters": {
                    "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 50},
                    "oversold_threshold": {"type": "float", "default": 30, "min": 10, "max": 40},
                    "overbought_threshold": {"type": "float", "default": 70, "min": 60, "max": 90}
                }
            },
            {
                "name": "MACD",
                "description": "MACD Strategy",
                "parameters": {
                    "fast_period": {"type": "int", "default": 12, "min": 5, "max": 20},
                    "slow_period": {"type": "int", "default": 26, "min": 20, "max": 50},
                    "signal_period": {"type": "int", "default": 9, "min": 5, "max": 15}
                }
            },
            {
                "name": "MultiIndicator",
                "description": "Multi-Indicator Strategy",
                "parameters": {}
            }
        ]
    }


@app.post("/api/strategies/signal", response_model=TradingSignalResponse)
async def get_trading_signal(
    strategy_name: str,
    symbol: str = "BTCUSDT",
    parameters: Dict[str, Any] = None
):
    """Obtener señal de trading de una estrategia."""
    try:
        # Obtener datos de mercado
        ohlcv_data = await market_data_manager.get_ohlcv(symbol, "1h", 200)
        if not ohlcv_data:
            raise HTTPException(status_code=404, detail="No hay datos de mercado")
        
        # Convertir a DataFrame
        import pandas as pd
        data = []
        for candle in ohlcv_data:
            data.append({
                "timestamp": candle.timestamp,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume
            })
        
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        
        # Crear estrategia
        if strategy_name.lower() == "rsi":
            params = parameters or {}
            strategy = RSIStrategy(
                rsi_period=params.get("rsi_period", 14),
                oversold_threshold=params.get("oversold_threshold", 30),
                overbought_threshold=params.get("overbought_threshold", 70)
            )
        elif strategy_name.lower() == "macd":
            params = parameters or {}
            strategy = MACDStrategy(
                fast_period=params.get("fast_period", 12),
                slow_period=params.get("slow_period", 26),
                signal_period=params.get("signal_period", 9)
            )
        elif strategy_name.lower() == "multiindicator":
            strategy = MultiIndicatorStrategy()
        else:
            raise HTTPException(status_code=400, detail="Estrategia no soportada")
        
        # Obtener señal
        signal = strategy.analyze(df)
        if not signal:
            raise HTTPException(status_code=404, detail="No se pudo generar señal")
        
        return TradingSignalResponse(
            signal=signal.signal.value,
            strength=signal.strength,
            price=signal.price,
            timestamp=signal.timestamp.isoformat(),
            reason=signal.reason,
            indicators=signal.indicators
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE SALUD Y ESTADO
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Verificar salud del sistema."""
    try:
        # Verificar componentes críticos
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "market_data": market_data_manager is not None,
                "trading_agent": trading_agent is not None and trading_agent.state.is_running,
                "research_agent": research_agent is not None and research_agent.is_running,
                "optimizer_agent": optimizer_agent is not None and optimizer_agent.is_running,
                "backtest_engine": backtest_engine is not None
            }
        }
        
        # Verificar si todos los componentes están funcionando
        all_healthy = all(health_status["components"].values())
        health_status["status"] = "healthy" if all_healthy else "degraded"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# EJECUTAR SERVIDOR
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )