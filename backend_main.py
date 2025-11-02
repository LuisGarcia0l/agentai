#!/usr/bin/env python3
"""
🚀 AI Trading System - Backend Only Entry Point

Punto de entrada dedicado para el backend API sin dependencias de frontend.
Ejecuta solo la API FastAPI y los agentes de trading.

Author: Luis (AI Trading System)
Version: 2.0.0
"""

import asyncio
import uvicorn
from pathlib import Path
import sys

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from utils.config.settings import settings
from utils.logging.logger import setup_logging, trading_logger


def main():
    """Función principal para ejecutar solo el backend."""
    print("=" * 80)
    print("🚀 AI TRADING SYSTEM - BACKEND API v2.0")
    print("=" * 80)
    print("Backend API puro sin dependencias de frontend")
    print(f"Modo: {settings.TRADING_MODE.upper()}")
    print(f"Exchange: {settings.DEFAULT_EXCHANGE.upper()}")
    print(f"API Host: {settings.API_HOST}")
    print(f"API Port: {settings.API_PORT}")
    print("=" * 80)
    print("Características del Backend:")
    print("• API REST con FastAPI")
    print("• WebSocket para datos en tiempo real")
    print("• Agentes IA autónomos")
    print("• Análisis técnico automatizado")
    print("• Backtesting y optimización")
    print("• Gestión de riesgo inteligente")
    print("=" * 80)
    print("⚠️  ADVERTENCIA: Siempre usa paper trading primero")
    print("=" * 80)
    
    # Configurar logging
    setup_logging(level=settings.LOG_LEVEL)
    
    try:
        # Ejecutar servidor FastAPI
        trading_logger.logger.info("🚀 Iniciando servidor FastAPI...")
        
        uvicorn.run(
            "api.main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True
        )
        
    except KeyboardInterrupt:
        trading_logger.logger.info("🛑 Backend detenido por el usuario")
        print("\n👋 ¡Backend detenido!")
    except Exception as e:
        trading_logger.logger.error(f"❌ Error crítico en backend: {e}")
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())