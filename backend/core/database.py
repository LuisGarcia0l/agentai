"""
Configuración y modelos de base de datos
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
import logging

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Base para modelos
Base = declarative_base()

# Configuración de base de datos
if settings.DATABASE_URL.startswith("sqlite"):
    # Para SQLite, usar versión async
    DATABASE_URL = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG)
else:
    # Para PostgreSQL u otras bases de datos
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# Session maker
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class TradingSession(Base):
    """Modelo para sesiones de trading"""
    __tablename__ = "trading_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active, paused, stopped
    initial_balance = Column(Float, default=1000.0)
    current_balance = Column(Float, default=1000.0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    active_strategies = Column(JSON, default=list)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Trade(Base):
    """Modelo para trades ejecutados"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True)
    trade_id = Column(String(100), unique=True, index=True)
    symbol = Column(String(20), index=True)
    side = Column(String(10))  # BUY, SELL
    order_type = Column(String(20))  # MARKET, LIMIT, STOP_LOSS, etc.
    quantity = Column(Float)
    price = Column(Float)
    executed_price = Column(Float, nullable=True)
    executed_quantity = Column(Float, nullable=True)
    status = Column(String(20))  # NEW, FILLED, CANCELED, REJECTED
    strategy = Column(String(50), index=True)
    agent = Column(String(50), index=True)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    pnl = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Strategy(Base):
    """Modelo para estrategias de trading"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(Text)
    strategy_type = Column(String(50))  # technical, ml, hybrid
    parameters = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    performance_metrics = Column(JSON, default=dict)
    backtest_results = Column(JSON, default=dict)
    created_by = Column(String(50), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AgentActivity(Base):
    """Modelo para actividad de agentes"""
    __tablename__ = "agent_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(50), index=True)
    activity_type = Column(String(50))  # analysis, trade, optimization, research
    description = Column(Text)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    execution_time = Column(Float)  # en segundos
    status = Column(String(20))  # success, error, timeout
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class MarketData(Base):
    """Modelo para datos de mercado"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    timestamp = Column(DateTime, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)
    timeframe = Column(String(10))  # 1m, 5m, 15m, 1h, 4h, 1d
    indicators = Column(JSON, default=dict)  # RSI, MACD, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

class BacktestResult(Base):
    """Modelo para resultados de backtesting"""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(String(100), unique=True, index=True)
    strategy_name = Column(String(100), index=True)
    symbol = Column(String(20), index=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    initial_capital = Column(Float)
    final_capital = Column(Float)
    total_return = Column(Float)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    parameters = Column(JSON, default=dict)
    detailed_results = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemMetrics(Base):
    """Modelo para métricas del sistema"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), index=True)
    metric_value = Column(Float)
    metric_type = Column(String(50))  # counter, gauge, histogram
    labels = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

async def init_db():
    """Inicializar base de datos y crear tablas"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        raise

async def get_db() -> AsyncSession:
    """Obtener sesión de base de datos"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

class DatabaseManager:
    """Manager para operaciones de base de datos"""
    
    @staticmethod
    async def create_trading_session(session_data: Dict[str, Any]) -> TradingSession:
        """Crear nueva sesión de trading"""
        async with AsyncSessionLocal() as db:
            session = TradingSession(**session_data)
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
    
    @staticmethod
    async def get_active_trading_session() -> Optional[TradingSession]:
        """Obtener sesión de trading activa"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                "SELECT * FROM trading_sessions WHERE status = 'active' ORDER BY created_at DESC LIMIT 1"
            )
            return result.first()
    
    @staticmethod
    async def record_trade(trade_data: Dict[str, Any]) -> Trade:
        """Registrar un trade"""
        async with AsyncSessionLocal() as db:
            trade = Trade(**trade_data)
            db.add(trade)
            await db.commit()
            await db.refresh(trade)
            return trade
    
    @staticmethod
    async def get_strategy_performance(strategy_name: str) -> Dict[str, Any]:
        """Obtener métricas de performance de una estrategia"""
        async with AsyncSessionLocal() as db:
            # Implementar consulta de performance
            # Por ahora retornar datos mock
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "sharpe_ratio": 0.0
            }
    
    @staticmethod
    async def log_agent_activity(activity_data: Dict[str, Any]) -> AgentActivity:
        """Registrar actividad de agente"""
        async with AsyncSessionLocal() as db:
            activity = AgentActivity(**activity_data)
            db.add(activity)
            await db.commit()
            await db.refresh(activity)
            return activity