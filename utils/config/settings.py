"""
⚙️ Configuración del Sistema de Trading

Manejo centralizado de todas las configuraciones usando Pydantic Settings.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """Configuración principal del sistema."""
    
    # =============================================================================
    # CONFIGURACIÓN GENERAL
    # =============================================================================
    
    ENVIRONMENT: str = Field(default="development", description="Entorno de ejecución")
    DEBUG: bool = Field(default=True, description="Modo debug")
    LOG_LEVEL: str = Field(default="INFO", description="Nivel de logging")
    SECRET_KEY: str = Field(default="change-this-secret-key", description="Clave secreta")
    
    # =============================================================================
    # CONFIGURACIÓN DE TRADING
    # =============================================================================
    
    TRADING_MODE: str = Field(default="paper", description="Modo de trading: paper o live")
    DEFAULT_EXCHANGE: str = Field(default="binance", description="Exchange por defecto")
    DEFAULT_SYMBOL: str = Field(default="BTCUSDT", description="Símbolo por defecto")
    
    # Gestión de riesgo
    MAX_POSITION_SIZE: float = Field(default=0.02, description="Tamaño máximo de posición (2%)")
    MAX_DAILY_LOSS: float = Field(default=0.05, description="Pérdida máxima diaria (5%)")
    STOP_LOSS_PERCENT: float = Field(default=0.02, description="Stop loss (2%)")
    TAKE_PROFIT_PERCENT: float = Field(default=0.04, description="Take profit (4%)")
    
    # =============================================================================
    # APIS DE EXCHANGES
    # =============================================================================
    
    # Binance
    BINANCE_API_KEY: Optional[str] = Field(default=None, description="Binance API Key")
    BINANCE_SECRET_KEY: Optional[str] = Field(default=None, description="Binance Secret Key")
    BINANCE_TESTNET: bool = Field(default=True, description="Usar Binance testnet")
    
    # Alpaca
    ALPACA_API_KEY: Optional[str] = Field(default=None, description="Alpaca API Key")
    ALPACA_SECRET_KEY: Optional[str] = Field(default=None, description="Alpaca Secret Key")
    ALPACA_BASE_URL: str = Field(
        default="https://paper-api.alpaca.markets", 
        description="Alpaca base URL"
    )
    
    # =============================================================================
    # APIS DE IA
    # =============================================================================
    
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API Key")
    
    # =============================================================================
    # BASE DE DATOS
    # =============================================================================
    
    DATABASE_URL: str = Field(
        default="sqlite:///./trading.db", 
        description="URL de la base de datos"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    
    # =============================================================================
    # DASHBOARD Y API
    # =============================================================================
    
    DASHBOARD_HOST: str = Field(default="0.0.0.0", description="Host del dashboard")
    DASHBOARD_PORT: int = Field(default=8501, description="Puerto del dashboard")
    API_HOST: str = Field(default="0.0.0.0", description="Host de la API")
    API_PORT: int = Field(default=8000, description="Puerto de la API")
    
    # =============================================================================
    # CONFIGURACIÓN DE AGENTES
    # =============================================================================
    
    AGENT_UPDATE_INTERVAL: int = Field(default=300, description="Intervalo de actualización (segundos)")
    RESEARCH_AGENT_ENABLED: bool = Field(default=True, description="Habilitar Research Agent")
    OPTIMIZER_AGENT_ENABLED: bool = Field(default=True, description="Habilitar Optimizer Agent")
    RISK_AGENT_ENABLED: bool = Field(default=True, description="Habilitar Risk Agent")
    TRADING_AGENT_ENABLED: bool = Field(default=False, description="Habilitar Trading Agent")
    
    # =============================================================================
    # MACHINE LEARNING
    # =============================================================================
    
    ML_MODEL_RETRAIN_INTERVAL: int = Field(default=86400, description="Reentrenamiento ML (segundos)")
    STRATEGY_OPTIMIZATION_INTERVAL: int = Field(default=3600, description="Optimización estrategias (segundos)")
    
    # =============================================================================
    # BACKTESTING
    # =============================================================================
    
    BACKTEST_START_DATE: str = Field(default="2023-01-01", description="Fecha inicio backtest")
    BACKTEST_END_DATE: str = Field(default="2024-12-31", description="Fecha fin backtest")
    BACKTEST_INITIAL_CAPITAL: float = Field(default=10000.0, description="Capital inicial backtest")
    
    # =============================================================================
    # NOTIFICACIONES
    # =============================================================================
    
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(default=None, description="Token del bot de Telegram")
    TELEGRAM_CHAT_ID: Optional[str] = Field(default=None, description="Chat ID de Telegram")
    DISCORD_WEBHOOK_URL: Optional[str] = Field(default=None, description="Webhook de Discord")
    
    # Email
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="Host SMTP")
    SMTP_PORT: int = Field(default=587, description="Puerto SMTP")
    SMTP_USER: Optional[str] = Field(default=None, description="Usuario SMTP")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="Password SMTP")
    NOTIFICATION_EMAIL: Optional[str] = Field(default=None, description="Email de notificaciones")
    
    class Config:
        """Configuración de Pydantic."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignorar campos extra del .env
    
    @property
    def is_production(self) -> bool:
        """Verificar si estamos en producción."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_live_trading(self) -> bool:
        """Verificar si estamos en trading en vivo."""
        return self.TRADING_MODE.lower() == "live"
    
    @property
    def project_root(self) -> Path:
        """Obtener la ruta raíz del proyecto."""
        return Path(__file__).parent.parent.parent
    
    def get_exchange_config(self, exchange: str) -> dict:
        """Obtener configuración específica del exchange."""
        configs = {
            "binance": {
                "api_key": self.BINANCE_API_KEY,
                "secret": self.BINANCE_SECRET_KEY,
                "testnet": self.BINANCE_TESTNET,
                "sandbox": self.BINANCE_TESTNET
            },
            "alpaca": {
                "api_key": self.ALPACA_API_KEY,
                "secret": self.ALPACA_SECRET_KEY,
                "base_url": self.ALPACA_BASE_URL
            }
        }
        
        return configs.get(exchange.lower(), {})
    
    def validate_trading_config(self) -> List[str]:
        """Validar configuración de trading."""
        errors = []
        
        if self.is_live_trading:
            if not self.BINANCE_API_KEY and self.DEFAULT_EXCHANGE == "binance":
                errors.append("BINANCE_API_KEY requerida para trading en vivo")
            
            if not self.ALPACA_API_KEY and self.DEFAULT_EXCHANGE == "alpaca":
                errors.append("ALPACA_API_KEY requerida para trading en vivo")
        
        if self.MAX_POSITION_SIZE > 0.1:  # 10%
            errors.append("MAX_POSITION_SIZE muy alto (>10%)")
        
        if self.STOP_LOSS_PERCENT > 0.1:  # 10%
            errors.append("STOP_LOSS_PERCENT muy alto (>10%)")
        
        return errors


# Instancia global de configuración
settings = Settings()