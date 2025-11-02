"""
Configuración del sistema AutoDev Trading Studio
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Configuración principal del sistema"""
    
    # Configuración de la aplicación
    APP_NAME: str = "AutoDev Trading Studio"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Configuración del servidor
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Configuración de base de datos
    DATABASE_URL: str = Field(default="sqlite:///./trading_studio.db", env="DATABASE_URL")
    
    # Configuración de Binance Testnet
    BINANCE_TESTNET_API_KEY: str = Field(default="", env="BINANCE_TESTNET_API_KEY")
    BINANCE_TESTNET_SECRET_KEY: str = Field(default="", env="BINANCE_TESTNET_SECRET_KEY")
    BINANCE_TESTNET_BASE_URL: str = "https://testnet.binance.vision"
    
    # Configuración de OpenAI (para agentes IA)
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    # Configuración de Anthropic Claude (alternativa)
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")
    
    # Configuración de agentes
    MAX_CONCURRENT_AGENTS: int = Field(default=5, env="MAX_CONCURRENT_AGENTS")
    AGENT_EXECUTION_TIMEOUT: int = Field(default=300, env="AGENT_EXECUTION_TIMEOUT")  # 5 minutos
    
    # Configuración de trading
    DEFAULT_TRADING_PAIR: str = Field(default="BTCUSDT", env="DEFAULT_TRADING_PAIR")
    MAX_POSITION_SIZE: float = Field(default=0.1, env="MAX_POSITION_SIZE")  # 10% del capital
    DEFAULT_STOP_LOSS: float = Field(default=0.02, env="DEFAULT_STOP_LOSS")  # 2%
    DEFAULT_TAKE_PROFIT: float = Field(default=0.04, env="DEFAULT_TAKE_PROFIT")  # 4%
    
    # Configuración de riesgo
    MAX_DAILY_LOSS: float = Field(default=0.05, env="MAX_DAILY_LOSS")  # 5% pérdida máxima diaria
    MAX_DRAWDOWN: float = Field(default=0.15, env="MAX_DRAWDOWN")  # 15% drawdown máximo
    
    # Configuración de backtesting
    BACKTEST_START_DATE: str = Field(default="2023-01-01", env="BACKTEST_START_DATE")
    BACKTEST_END_DATE: str = Field(default="2024-01-01", env="BACKTEST_END_DATE")
    
    # Configuración de logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/trading_studio.log", env="LOG_FILE")
    
    # Configuración de Redis (para caché y sesiones)
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Configuración de WebSocket
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    
    # Configuración de monitoreo
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    
    # Configuración de alertas
    TELEGRAM_BOT_TOKEN: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = Field(default="", env="TELEGRAM_CHAT_ID")
    
    # Configuración de seguridad
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Configuración de desarrollo
    RELOAD: bool = Field(default=True, env="RELOAD")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_binance_config(self) -> dict:
        """Obtener configuración de Binance Testnet"""
        return {
            "api_key": self.BINANCE_TESTNET_API_KEY,
            "secret_key": self.BINANCE_TESTNET_SECRET_KEY,
            "base_url": self.BINANCE_TESTNET_BASE_URL,
            "testnet": True
        }
    
    def get_llm_config(self) -> dict:
        """Obtener configuración del modelo de lenguaje"""
        if self.OPENAI_API_KEY:
            return {
                "provider": "openai",
                "api_key": self.OPENAI_API_KEY,
                "model": self.OPENAI_MODEL
            }
        elif self.ANTHROPIC_API_KEY:
            return {
                "provider": "anthropic",
                "api_key": self.ANTHROPIC_API_KEY,
                "model": "claude-3-sonnet-20240229"
            }
        else:
            # Configuración por defecto para desarrollo (sin API keys)
            return {
                "provider": "mock",
                "model": "mock-llm"
            }

# Instancia global de configuración
settings = Settings()

# Crear directorios necesarios
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("backtest_results", exist_ok=True)