"""
🔧 Logger Simplificado - Fallback si structlog no está disponible
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logging(level="INFO"):
    """Configurar logging básico."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('trading.log')
        ]
    )
    return logging.getLogger("trading")

# Logger global
trading_logger = setup_logging()

def log_agent_action(agent_id: str, action: str, result: str, **kwargs):
    """Log de acciones de agentes."""
    message = f"Agent {agent_id}: {action} -> {result}"
    if kwargs:
        message += f" | {kwargs}"
    trading_logger.info(message)

def log_trade_execution(symbol: str, side: str, quantity: float, price: float, **kwargs):
    """Log de ejecución de trades."""
    message = f"TRADE: {side} {quantity} {symbol} @ {price}"
    if kwargs:
        message += f" | {kwargs}"
    trading_logger.info(message)

def log_strategy_signal(strategy: str, symbol: str, signal: str, confidence: float, **kwargs):
    """Log de señales de estrategia."""
    message = f"SIGNAL: {strategy} -> {signal} {symbol} (confidence: {confidence:.2f})"
    if kwargs:
        message += f" | {kwargs}"
    trading_logger.info(message)

def log_error(error: Exception, context: str = "", **kwargs):
    """Log de errores."""
    message = f"ERROR in {context}: {str(error)}"
    if kwargs:
        message += f" | {kwargs}"
    trading_logger.error(message)

def log_system_event(event: str, details: str = "", **kwargs):
    """Log de eventos del sistema."""
    message = f"SYSTEM: {event}"
    if details:
        message += f" - {details}"
    if kwargs:
        message += f" | {kwargs}"
    trading_logger.info(message)

# Alias para compatibilidad
logger = trading_logger