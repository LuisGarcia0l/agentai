"""
Configuración de logging para AutoDev Trading Studio
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

from backend.core.config import settings

def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configurar el sistema de logging
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    # Usar nivel de configuración si no se especifica
    if log_level is None:
        log_level = settings.LOG_LEVEL
    
    # Crear directorio de logs si no existe
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configurar formato de logging
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)-20s | "
        "%(funcName)-15s:%(lineno)-3d | %(message)s"
    )
    
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configurar logging básico
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[]
    )
    
    # Obtener logger raíz
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Handler para archivo con rotación
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Archivo siempre en DEBUG
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Configurar loggers específicos
    configure_specific_loggers()
    
    # Log inicial
    logger = logging.getLogger(__name__)
    logger.info(f"Sistema de logging configurado - Nivel: {log_level}")

def configure_specific_loggers():
    """Configurar loggers específicos para diferentes componentes"""
    
    # Reducir verbosidad de librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Configurar loggers de trading
    trading_logger = logging.getLogger("trading")
    trading_logger.setLevel(logging.INFO)
    
    # Configurar loggers de agentes
    agents_logger = logging.getLogger("agents")
    agents_logger.setLevel(logging.INFO)
    
    # Configurar logger de backtesting
    backtest_logger = logging.getLogger("backtesting")
    backtest_logger.setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """
    Obtener logger con nombre específico
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)

class TradingLoggerAdapter(logging.LoggerAdapter):
    """Adapter para agregar contexto de trading a los logs"""
    
    def process(self, msg, kwargs):
        """Procesar mensaje agregando contexto"""
        context = self.extra
        
        if context:
            context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
            return f"[{context_str}] {msg}", kwargs
        
        return msg, kwargs

def get_trading_logger(symbol: str = None, strategy: str = None, agent: str = None) -> TradingLoggerAdapter:
    """
    Obtener logger específico para trading con contexto
    
    Args:
        symbol: Símbolo de trading (ej: BTCUSDT)
        strategy: Nombre de la estrategia
        agent: Nombre del agente
        
    Returns:
        Logger adapter con contexto
    """
    base_logger = logging.getLogger("trading")
    
    context = {}
    if symbol:
        context["symbol"] = symbol
    if strategy:
        context["strategy"] = strategy
    if agent:
        context["agent"] = agent
    
    return TradingLoggerAdapter(base_logger, context)

# Configurar logging al importar el módulo
if not logging.getLogger().handlers:
    setup_logging()