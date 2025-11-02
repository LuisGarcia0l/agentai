#!/usr/bin/env python3
"""
🤖 AI Trading System - Backend Entry Point

Sistema de trading avanzado con agentes IA autónomos.
Backend puro sin dependencias de frontend.

Author: Luis (AI Trading System)
Version: 2.0.0
"""

import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from utils.config.settings import settings
from utils.logging.logger import setup_logging, trading_logger
from agents.trading_agent.agent import TradingAgent
from data.feeds.market_data import MarketDataManager


class AITradingSystem:
    """Sistema principal de trading con agentes IA - Backend Only."""
    
    def __init__(self):
        """Inicializar el sistema de trading."""
        self.logger = setup_logging(level=settings.LOG_LEVEL)
        self.market_data = MarketDataManager()
        self.trading_agent: Optional[TradingAgent] = None
        self.api_process = None
        self.is_running = False
        
    async def initialize(self):
        """Inicializar todos los componentes del sistema."""
        trading_logger.logger.info("🚀 Inicializando AI Trading System...")
        
        # Inicializar conexiones de datos
        await self.market_data.initialize()
        
        # Inicializar agente de trading
        self.trading_agent = TradingAgent(
            market_data=self.market_data,
            settings=settings
        )
        await self.trading_agent.initialize()
        
        trading_logger.logger.info("✅ Sistema inicializado correctamente")
    
    def start_api_server(self):
        """Iniciar servidor FastAPI."""
        try:
            trading_logger.logger.info("🌐 Iniciando servidor FastAPI...")
            self.api_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "api.main:app",
                "--host", settings.API_HOST,
                "--port", str(settings.API_PORT),
                "--reload" if settings.DEBUG else "--no-reload"
            ])
            trading_logger.logger.info(f"✅ API iniciada en http://{settings.API_HOST}:{settings.API_PORT}")
        except Exception as e:
            trading_logger.logger.error(f"❌ Error iniciando API: {e}")
    

    
    def show_access_urls(self):
        """Mostrar URLs de acceso."""
        print("\n" + "=" * 80)
        print("🌐 URLS DE ACCESO - BACKEND API")
        print("=" * 80)
        print(f"🚀 API FastAPI:        http://{settings.API_HOST}:{settings.API_PORT}")
        print(f"📈 API Docs:           http://{settings.API_HOST}:{settings.API_PORT}/docs")
        print(f"📋 API Redoc:          http://{settings.API_HOST}:{settings.API_PORT}/redoc")
        print("=" * 80)
        print("💡 Usa Ctrl+C para detener el sistema")
        print("💡 Frontend React debe ejecutarse por separado")
        print("=" * 80 + "\n")
        
    async def run(self):
        """Ejecutar el sistema principal."""
        self.is_running = True
        
        try:
            # Inicializar sistema
            await self.initialize()
            
            # Mostrar modo de trading
            if settings.TRADING_MODE == "paper":
                trading_logger.logger.info("📊 Ejecutando en modo Paper Trading")
            else:
                trading_logger.logger.warning("⚠️ Ejecutando en modo LIVE TRADING")
            
            # Iniciar servidor API
            self.start_api_server()
            time.sleep(2)  # Esperar a que inicie la API
            
            # Mostrar URLs
            self.show_access_urls()
            
            # Iniciar agente de trading si está habilitado
            if settings.TRADING_AGENT_ENABLED:
                trading_logger.logger.info("🤖 Iniciando Trading Agent...")
                asyncio.create_task(self.trading_agent.run())
            
            # Mantener el sistema ejecutándose
            while self.is_running:
                await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            trading_logger.logger.info("🛑 Sistema detenido por el usuario")
        except Exception as e:
            trading_logger.logger.error(f"❌ Error crítico: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Limpiar recursos al cerrar."""
        trading_logger.logger.info("🧹 Limpiando recursos...")
        self.is_running = False
        
        # Detener procesos
        if self.api_process:
            self.api_process.terminate()
            self.api_process.wait()
        
        # Detener agente
        if self.trading_agent:
            await self.trading_agent.stop()
        
        # Cerrar conexiones
        await self.market_data.close()
        trading_logger.logger.info("✅ Limpieza completada")


def main():
    """Función principal."""
    print("=" * 80)
    print("🤖 AI TRADING SYSTEM v2.0 - BACKEND")
    print("=" * 80)
    print("Sistema de trading avanzado con agentes IA - Backend API")
    print(f"Modo: {settings.TRADING_MODE.upper()}")
    print(f"Exchange: {settings.DEFAULT_EXCHANGE.upper()}")
    print(f"Símbolo: {settings.DEFAULT_SYMBOL}")
    print(f"Entorno: {settings.ENVIRONMENT.upper()}")
    print("=" * 80)
    print("Características:")
    print("• API REST con FastAPI")
    print("• Análisis técnico automatizado")
    print("• Agentes IA autónomos")
    print("• Gestión de riesgo inteligente")
    print("• Backtesting avanzado")
    print("• Optimización automática")
    print("• WebSocket para datos en tiempo real")
    print("=" * 80)
    print("⚠️  ADVERTENCIA: Siempre usa paper trading primero")
    print("⚠️  NOTA: Este es solo el backend. Frontend React por separado.")
    print("=" * 80)
    
    # Crear y ejecutar el sistema
    system = AITradingSystem()
    
    try:
        asyncio.run(system.run())
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())