"""
AutoDev Trading Studio - Backend Principal
Sistema de trading autónomo con agentes IA especializados
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from backend.core.config import settings
from backend.core.database import init_db
from backend.core.logging_config import setup_logging
from backend.agents.agent_manager import AgentManager
from backend.api.routes import trading
from backend.services.websocket_manager import WebSocketManager
from backend.services.binance_service import BinanceService
from backend.services.llm_service import LLMService
from backend.services.risk_manager import RiskManager

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Managers y servicios globales
agent_manager: AgentManager = None
websocket_manager: WebSocketManager = None
binance_service: BinanceService = None
llm_service: LLMService = None
risk_manager: RiskManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    global agent_manager, websocket_manager, binance_service, llm_service, risk_manager
    
    logger.info("🚀 Iniciando AutoDev Trading Studio...")
    
    try:
        # Inicializar base de datos
        await init_db()
        logger.info("✅ Base de datos inicializada")
        
        # Inicializar servicios
        websocket_manager = WebSocketManager()
        logger.info("✅ WebSocket Manager inicializado")
        
        binance_service = BinanceService()
        await binance_service.initialize()
        logger.info("✅ Binance Service inicializado")
        
        llm_service = LLMService()
        await llm_service.initialize()
        logger.info("✅ LLM Service inicializado")
        
        risk_manager = RiskManager()
        await risk_manager.initialize()
        logger.info("✅ Risk Manager inicializado")
        
        # Inicializar agentes IA (último)
        agent_manager = AgentManager()
        await agent_manager.initialize()
        logger.info("✅ Agent Manager inicializado")
        
        # Iniciar servicios en background
        await agent_manager.start_monitoring()
        logger.info("✅ Monitoreo del sistema iniciado")
        
        logger.info("🎉 AutoDev Trading Studio iniciado correctamente!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error durante el inicio: {e}")
        raise
    finally:
        # Cleanup
        logger.info("🛑 Cerrando sistema...")
        
        if agent_manager:
            await agent_manager.shutdown()
        
        if websocket_manager:
            await websocket_manager.shutdown()
        
        if binance_service:
            await binance_service.close()
        
        logger.info("✅ Sistema cerrado correctamente")

# Crear aplicación FastAPI
app = FastAPI(
    title="AutoDev Trading Studio",
    description="Sistema de trading autónomo con agentes IA especializados",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])

@app.get("/")
async def root():
    """Endpoint de salud del sistema"""
    return {
        "message": "AutoDev Trading Studio API",
        "version": "1.0.0",
        "status": "running",
        "agents_active": agent_manager.get_active_agents_count() if agent_manager else 0
    }

@app.get("/health")
async def health():
    """Endpoint de salud simple"""
    return {"status": "healthy", "service": "AutoDev Trading Studio"}

@app.get("/api/health")
async def health_check():
    """Verificación de salud detallada"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "services": {
                "database": "connected",
                "binance_testnet": "connected",
                "agents": "active" if agent_manager and agent_manager.is_running else "inactive"
            }
        }
        
        if agent_manager:
            health_status["agents_info"] = await agent_manager.get_agents_status()
            
        return health_status
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail="Sistema no disponible")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para comunicación en tiempo real"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Mantener conexión activa
            data = await websocket.receive_text()
            # Procesar mensajes del cliente si es necesario
            await websocket_manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )

def get_agent_manager() -> AgentManager:
    """Obtener instancia del manager de agentes"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent Manager no inicializado")
    return agent_manager

def get_websocket_manager() -> WebSocketManager:
    """Obtener instancia del manager de WebSocket"""
    if not websocket_manager:
        raise HTTPException(status_code=503, detail="WebSocket Manager no inicializado")
    return websocket_manager

def get_binance_service() -> BinanceService:
    """Obtener instancia del servicio de Binance"""
    if not binance_service:
        raise HTTPException(status_code=503, detail="Binance Service no inicializado")
    return binance_service

def get_llm_service() -> LLMService:
    """Obtener instancia del servicio LLM"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="LLM Service no inicializado")
    return llm_service

def get_risk_manager() -> RiskManager:
    """Obtener instancia del gestor de riesgo"""
    if not risk_manager:
        raise HTTPException(status_code=503, detail="Risk Manager no inicializado")
    return risk_manager

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )