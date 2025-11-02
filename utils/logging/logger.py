"""
📝 Sistema de Logging Avanzado

Sistema de logging estructurado con colores, métricas y rotación automática.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import structlog
from rich.logging import RichHandler
from rich.console import Console


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = True
) -> logging.Logger:
    """
    Configurar el sistema de logging.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_file: Archivo de log opcional
        structured: Usar logging estructurado
    
    Returns:
        Logger configurado
    """
    
    # Crear directorio de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar nivel
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configurar handlers
    handlers = []
    
    # Handler para consola con Rich (colores y formato bonito)
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=True,
        show_path=True,
        markup=True,
        rich_tracebacks=True
    )
    console_handler.setLevel(log_level)
    handlers.append(console_handler)
    
    # Handler para archivo si se especifica
    if log_file:
        file_handler = logging.FileHandler(
            log_dir / log_file,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    # Configurar logging básico
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format="%(message)s"
    )
    
    if structured:
        # Configurar structlog para logging estructurado
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Crear logger principal
    logger = logging.getLogger("ai_trading_system")
    
    # Reducir verbosidad de librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("ccxt").setLevel(logging.WARNING)
    
    return logger


class TradingLogger:
    """Logger especializado para trading con métricas."""
    
    def __init__(self, name: str = "trading"):
        self.logger = logging.getLogger(name)
        self.structured_logger = structlog.get_logger(name)
    
    def trade_signal(self, symbol: str, action: str, price: float, reason: str):
        """Log de señal de trading."""
        self.structured_logger.info(
            "trade_signal",
            symbol=symbol,
            action=action,
            price=price,
            reason=reason,
            timestamp=datetime.now().isoformat()
        )
    
    def trade_executed(self, symbol: str, action: str, quantity: float, 
                      price: float, order_id: str):
        """Log de trade ejecutado."""
        self.structured_logger.info(
            "trade_executed",
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            order_id=order_id,
            timestamp=datetime.now().isoformat()
        )
    
    def risk_alert(self, message: str, severity: str = "medium", **kwargs):
        """Log de alerta de riesgo."""
        self.structured_logger.warning(
            "risk_alert",
            message=message,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )
    
    def performance_metric(self, metric_name: str, value: float, **kwargs):
        """Log de métrica de rendimiento."""
        self.structured_logger.info(
            "performance_metric",
            metric=metric_name,
            value=value,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )
    
    def agent_action(self, agent_name: str, action: str, result: str, **kwargs):
        """Log de acción de agente IA."""
        self.structured_logger.info(
            "agent_action",
            agent=agent_name,
            action=action,
            result=result,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )


class PerformanceLogger:
    """Logger para métricas de rendimiento del sistema."""
    
    def __init__(self):
        self.logger = structlog.get_logger("performance")
    
    def log_latency(self, operation: str, duration_ms: float):
        """Log de latencia de operación."""
        self.logger.info(
            "latency",
            operation=operation,
            duration_ms=duration_ms,
            timestamp=datetime.now().isoformat()
        )
    
    def log_throughput(self, operation: str, count: int, duration_s: float):
        """Log de throughput."""
        throughput = count / duration_s if duration_s > 0 else 0
        self.logger.info(
            "throughput",
            operation=operation,
            count=count,
            duration_s=duration_s,
            throughput=throughput,
            timestamp=datetime.now().isoformat()
        )
    
    def log_error_rate(self, operation: str, errors: int, total: int):
        """Log de tasa de errores."""
        error_rate = errors / total if total > 0 else 0
        self.logger.info(
            "error_rate",
            operation=operation,
            errors=errors,
            total=total,
            error_rate=error_rate,
            timestamp=datetime.now().isoformat()
        )


# Instancias globales
trading_logger = TradingLogger()
performance_logger = PerformanceLogger()