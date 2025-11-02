#!/usr/bin/env python3
"""
🤖 AI Trading System - Main Entry Point

Sistema de trading avanzado con agentes IA autónomos.
Combina análisis técnico, machine learning y optimización automática.

Author: Luis (AI Trading System)
Version: 1.0.0
"""

import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from utils.config.settings import settings

# Intentar importar logger avanzado, usar simple como fallback
try:
    from utils.logging.logger import setup_logging, trading_logger
except ImportError:
    print("⚠️ structlog no disponible, usando logger simple...")
    from utils.logging.simple_logger import setup_logging, trading_logger
from dashboard.streamlit_app.app import run_dashboard
from agents.trading_agent.agent import TradingAgent
from data.feeds.market_data import MarketDataManager


class AITradingSystem:
    """Sistema principal de trading con agentes IA."""
    
    def __init__(self):
        """Inicializar el sistema de trading."""
        self.logger = setup_logging(level=settings.LOG_LEVEL)
        self.market_data = MarketDataManager()
        self.trading_agent: Optional[TradingAgent] = None
        self.api_process = None
        self.frontend_process = None
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
    
    def start_frontend_server(self):
        """Iniciar servidor React."""
        try:
            frontend_path = Path(__file__).parent / "frontend"
            if frontend_path.exists():
                trading_logger.logger.info("⚛️ Iniciando frontend React...")
                
                # Verificar si npm está disponible
                try:
                    subprocess.run(["npm", "--version"], check=True, capture_output=True)
                    
                    # Instalar dependencias si es necesario
                    if not (frontend_path / "node_modules").exists():
                        trading_logger.logger.info("📦 Instalando dependencias...")
                        subprocess.run(["npm", "install"], cwd=frontend_path, check=True)
                    
                    # Iniciar servidor
                    self.frontend_process = subprocess.Popen([
                        "npm", "run", "dev"
                    ], cwd=frontend_path)
                    
                    trading_logger.logger.info("✅ Frontend iniciado en http://localhost:3000")
                except subprocess.CalledProcessError:
                    trading_logger.logger.warning("⚠️ npm no disponible, saltando frontend React")
            else:
                trading_logger.logger.warning("⚠️ Directorio frontend no encontrado")
        except Exception as e:
            trading_logger.logger.error(f"❌ Error iniciando frontend: {e}")
    
    def start_streamlit_dashboard(self):
        """Iniciar dashboard Streamlit."""
        try:
            trading_logger.logger.info("📊 Iniciando dashboard Streamlit...")
            dashboard_path = Path(__file__).parent / "dashboard" / "streamlit_app" / "app.py"
            
            if dashboard_path.exists():
                subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run",
                    str(dashboard_path),
                    "--server.port", str(settings.DASHBOARD_PORT),
                    "--server.address", settings.DASHBOARD_HOST,
                    "--server.headless", "true"
                ])
                trading_logger.logger.info(f"✅ Streamlit iniciado en http://{settings.DASHBOARD_HOST}:{settings.DASHBOARD_PORT}")
        except Exception as e:
            trading_logger.logger.error(f"❌ Error iniciando Streamlit: {e}")
    
    def show_access_urls(self):
        """Mostrar URLs de acceso."""
        print("\n" + "=" * 80)
        print("🌐 URLS DE ACCESO")
        print("=" * 80)
        print(f"📊 Dashboard React:    http://localhost:3000")
        print(f"🚀 API FastAPI:        http://{settings.API_HOST}:{settings.API_PORT}")
        print(f"📈 API Docs:           http://{settings.API_HOST}:{settings.API_PORT}/docs")
        print(f"📋 Dashboard Streamlit: http://{settings.DASHBOARD_HOST}:{settings.DASHBOARD_PORT}")
        print("=" * 80)
        print("💡 Usa Ctrl+C para detener el sistema")
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
            
            # Iniciar servidores web
            self.start_api_server()
            time.sleep(2)  # Esperar a que inicie la API
            
            self.start_frontend_server()
            self.start_streamlit_dashboard()
            
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
        
        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process.wait()
        
        # Detener agente
        if self.trading_agent:
            await self.trading_agent.stop()
        
        # Cerrar conexiones
        await self.market_data.close()
        trading_logger.logger.info("✅ Limpieza completada")


def main():
    """Función principal."""
    print("=" * 80)
    print("🤖 AI TRADING SYSTEM v1.0")
    print("=" * 80)
    print("Sistema de trading avanzado con agentes IA")
    print(f"Modo: {settings.TRADING_MODE.upper()}")
    print(f"Exchange: {settings.DEFAULT_EXCHANGE.upper()}")
    print(f"Símbolo: {settings.DEFAULT_SYMBOL}")
    print(f"Entorno: {settings.ENVIRONMENT.upper()}")
    print("=" * 80)
    print("Características:")
    print("• Análisis técnico automatizado")
    print("• Agentes IA autónomos")
    print("• Gestión de riesgo inteligente")
    print("• Dashboard React + FastAPI")
    print("• Backtesting avanzado")
    print("• Optimización automática")
    print("=" * 80)
    print("⚠️  ADVERTENCIA: Siempre usa paper trading primero")
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