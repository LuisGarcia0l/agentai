# 🤖 AI Trading System - Guía Técnica Completa

## 📋 Índice

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Instalación y Configuración](#instalación-y-configuración)
3. [Componentes Principales](#componentes-principales)
4. [APIs y Integraciones](#apis-y-integraciones)
5. [Estrategias de Trading](#estrategias-de-trading)
6. [Agentes IA](#agentes-ia)
7. [Sistema de Backtesting](#sistema-de-backtesting)
8. [Gestión de Riesgo](#gestión-de-riesgo)
9. [Dashboard y Monitoreo](#dashboard-y-monitoreo)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

---

## 🏗️ Arquitectura del Sistema

### Visión General

El AI Trading System es una plataforma modular diseñada con arquitectura de microservicios que combina:

- **Análisis Técnico Tradicional**: RSI, MACD, Bollinger Bands
- **Machine Learning**: Modelos predictivos y optimización automática
- **Agentes IA Autónomos**: Investigación, optimización y ejecución
- **Gestión de Riesgo Inteligente**: Stop-loss dinámico y position sizing
- **Backtesting Avanzado**: Validación histórica con métricas detalladas

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Trading System                            │
├─────────────────────────────────────────────────────────────────┤
│  📱 Dashboard Layer                                             │
│  ├── Streamlit Web App                                         │
│  ├── FastAPI REST API                                          │
│  └── Real-time Monitoring                                      │
├─────────────────────────────────────────────────────────────────┤
│  🤖 AI Agents Layer                                            │
│  ├── Trading Agent      ├── Research Agent                    │
│  ├── Risk Agent         └── Optimizer Agent                   │
├─────────────────────────────────────────────────────────────────┤
│  🧠 Strategy Layer                                             │
│  ├── Technical Analysis ├── ML Models                         │
│  ├── Signal Generation  └── Multi-Indicator                   │
├─────────────────────────────────────────────────────────────────┤
│  💼 Execution Layer                                            │
│  ├── Order Management   ├── Paper Trading                     │
│  ├── Risk Management    └── Portfolio Management              │
├─────────────────────────────────────────────────────────────────┤
│  📊 Data Layer                                                 │
│  ├── Market Data Feeds  ├── Historical Data                   │
│  ├── Real-time Streams  └── Data Processing                   │
├─────────────────────────────────────────────────────────────────┤
│  🗄️ Storage Layer                                              │
│  ├── PostgreSQL         ├── Redis Cache                       │
│  ├── Time Series DB     └── File Storage                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Instalación y Configuración

### Prerrequisitos

- **Python 3.11+**
- **Docker & Docker Compose**
- **Git**
- **Cuenta en Exchange** (Binance recomendado)

### Instalación Rápida

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd ai-trading-system

# 2. Configurar entorno
cp .env.example .env
# Editar .env con tus API keys

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar con Docker
docker-compose up -d

# 5. O ejecutar localmente
python main.py
```

### Configuración Detallada

#### Variables de Entorno Críticas

```bash
# Exchange APIs
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
BINANCE_TESTNET=true  # Usar testnet inicialmente

# Trading Configuration
TRADING_MODE=paper    # paper | live
MAX_POSITION_SIZE=0.02  # 2% máximo por posición
STOP_LOSS_PERCENT=0.02  # 2% stop loss
TAKE_PROFIT_PERCENT=0.04  # 4% take profit

# AI Configuration
OPENAI_API_KEY=your_openai_key  # Para agentes IA
ANTHROPIC_API_KEY=your_claude_key  # Opcional
```

#### Base de Datos

```sql
-- Crear base de datos
CREATE DATABASE trading_db;
CREATE USER trading_user WITH PASSWORD 'trading_pass';
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;
```

---

## 🧩 Componentes Principales

### 1. Market Data Manager (`data/feeds/market_data.py`)

**Responsabilidades:**
- Conexión con múltiples exchanges
- Obtención de datos OHLCV en tiempo real
- Cache inteligente con TTL
- Manejo de rate limits

**Ejemplo de Uso:**
```python
from data.feeds.market_data import MarketDataManager

market_data = MarketDataManager()
await market_data.initialize()

# Obtener datos OHLCV
ohlcv = await market_data.get_ohlcv("BTCUSDT", "1h", 100)

# Obtener ticker actual
ticker = await market_data.get_ticker("BTCUSDT")
```

### 2. Technical Indicators (`strategies/technical/indicators.py`)

**Indicadores Implementados:**
- **RSI**: Relative Strength Index
- **MACD**: Moving Average Convergence Divergence
- **Bollinger Bands**: Bandas de volatilidad
- **SMA/EMA**: Medias móviles
- **Stochastic**: Oscilador estocástico
- **ATR**: Average True Range

**Ejemplo de Estrategia:**
```python
from strategies.technical.indicators import RSIStrategy

strategy = RSIStrategy(
    rsi_period=14,
    oversold_threshold=30,
    overbought_threshold=70
)

signal = strategy.analyze(market_data)
if signal.signal == SignalType.BUY:
    print(f"Señal de compra: {signal.reason}")
```

### 3. Backtest Engine (`backtesting/engine/backtest_engine.py`)

**Características:**
- Simulación realista con slippage y comisiones
- Múltiples tipos de órdenes
- Métricas avanzadas (Sharpe, Calmar, Drawdown)
- Análisis de trades detallado

**Ejemplo de Backtesting:**
```python
from backtesting.engine.backtest_engine import BacktestEngine

engine = BacktestEngine(
    initial_capital=10000,
    commission_rate=0.001,
    slippage=0.0001
)

results = engine.run_backtest(strategy, historical_data, "BTCUSDT")
print(f"Rendimiento: {results['total_return']:.2f}%")
```

### 4. Risk Manager (`risk_management/portfolio/risk_manager.py`)

**Funcionalidades:**
- Cálculo de Value at Risk (VaR)
- Position sizing inteligente
- Stop-loss dinámico
- Análisis de correlaciones
- Límites de drawdown

**Ejemplo de Gestión de Riesgo:**
```python
from risk_management.portfolio.risk_manager import RiskManager

risk_manager = RiskManager(settings)

# Evaluar si abrir posición
can_open, reason = risk_manager.should_open_position(
    symbol="BTCUSDT",
    position_size=0.1,
    entry_price=45000,
    portfolio_value=50000,
    current_positions={}
)
```

---

## 🔌 APIs y Integraciones

### Exchanges Soportados

| Exchange | Spot | Futures | Status |
|----------|------|---------|--------|
| Binance | ✅ | ✅ | Completo |
| Alpaca | ✅ | ❌ | Básico |
| Interactive Brokers | 🔄 | 🔄 | Planeado |

### Configuración de Exchange

```python
# Binance Configuration
exchange_config = {
    'binance': {
        'api_key': settings.BINANCE_API_KEY,
        'secret': settings.BINANCE_SECRET_KEY,
        'testnet': settings.BINANCE_TESTNET,
        'sandbox': True  # Para testing
    }
}
```

### Rate Limits y Mejores Prácticas

- **Binance**: 1200 requests/minute
- **Implementar exponential backoff**
- **Usar WebSockets para datos en tiempo real**
- **Cache inteligente para reducir llamadas**

---

## 📈 Estrategias de Trading

### Estrategias Implementadas

#### 1. RSI Strategy
```python
class RSIStrategy(TradingStrategy):
    def __init__(self, rsi_period=14, oversold=30, overbought=70):
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold
        self.overbought_threshold = overbought
    
    def analyze(self, df):
        rsi = self.indicators.rsi(df['close'], self.rsi_period)
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < self.oversold_threshold:
            return TradingSignal(SignalType.BUY, ...)
        elif current_rsi > self.overbought_threshold:
            return TradingSignal(SignalType.SELL, ...)
```

#### 2. MACD Strategy
- Detecta cruces de líneas MACD
- Confirma tendencias
- Filtra señales falsas

#### 3. Multi-Indicator Strategy
- Combina RSI, MACD y Bollinger Bands
- Sistema de votación ponderado
- Mayor precisión en señales

### Crear Estrategia Personalizada

```python
class MyCustomStrategy(TradingStrategy):
    def __init__(self, param1, param2):
        super().__init__("My Custom Strategy")
        self.param1 = param1
        self.param2 = param2
    
    def analyze(self, df):
        # Tu lógica personalizada aquí
        signal_strength = self.calculate_signal_strength(df)
        
        return TradingSignal(
            signal=SignalType.BUY,
            strength=signal_strength,
            price=df['close'].iloc[-1],
            timestamp=df.index[-1],
            reason="Custom logic triggered",
            indicators={"custom_metric": signal_strength}
        )
```

---

## 🤖 Agentes IA

### Trading Agent (`agents/trading_agent/agent.py`)

**Responsabilidades:**
- Análisis continuo del mercado
- Generación de decisiones de trading
- Ejecución de órdenes (paper/live)
- Monitoreo de rendimiento

**Ciclo de Vida:**
1. **Inicialización**: Cargar configuración y estado
2. **Análisis**: Evaluar datos de mercado
3. **Decisión**: Combinar señales y evaluar riesgo
4. **Ejecución**: Enviar órdenes al mercado
5. **Monitoreo**: Seguimiento de posiciones

### Configuración de Agentes

```python
# Configurar agente
agent = TradingAgent(
    market_data=market_data_manager,
    settings=settings,
    agent_id="trading_agent_001"
)

# Inicializar y ejecutar
await agent.initialize()
await agent.run()  # Bucle principal
```

### Agentes Futuros (Roadmap)

- **Research Agent**: Descubrimiento de nuevas estrategias
- **Optimizer Agent**: Optimización automática de parámetros
- **Risk Agent**: Monitoreo continuo de riesgo
- **News Agent**: Análisis de sentiment de noticias

---

## 🔬 Sistema de Backtesting

### Métricas Calculadas

| Métrica | Descripción | Fórmula |
|---------|-------------|---------|
| Total Return | Rendimiento total | (Final - Initial) / Initial * 100 |
| Sharpe Ratio | Rendimiento ajustado por riesgo | (Return - RiskFree) / Volatility |
| Max Drawdown | Pérdida máxima desde pico | Max((Peak - Valley) / Peak) |
| Win Rate | Porcentaje de trades ganadores | Winning Trades / Total Trades |
| Profit Factor | Ratio ganancia/pérdida | Gross Profit / Gross Loss |
| Calmar Ratio | Return anual / Max Drawdown | Annual Return / Max Drawdown |

### Ejemplo Completo de Backtesting

```python
# Configurar backtesting
engine = BacktestEngine(
    initial_capital=50000,
    commission_rate=0.001,  # 0.1%
    slippage=0.0001,       # 0.01%
    max_position_size=0.8   # 80% máximo
)

# Ejecutar múltiples estrategias
strategies = {
    'RSI': RSIStrategy(),
    'MACD': MACDStrategy(),
    'Multi': MultiIndicatorStrategy()
}

results = {}
for name, strategy in strategies.items():
    result = engine.run_backtest(strategy, data, "BTCUSDT")
    results[name] = result

# Comparar resultados
best_strategy = max(results.items(), key=lambda x: x[1]['sharpe_ratio'])
print(f"Mejor estrategia: {best_strategy[0]}")
```

---

## 🛡️ Gestión de Riesgo

### Niveles de Riesgo

```python
class RiskLevel(Enum):
    LOW = "low"        # < 30% risk score
    MEDIUM = "medium"  # 30-60% risk score
    HIGH = "high"      # 60-80% risk score
    CRITICAL = "critical"  # > 80% risk score
```

### Componentes de Riesgo

1. **Portfolio Risk**: Concentración de posiciones
2. **Position Risk**: Tamaño individual de posiciones
3. **Volatility Risk**: Volatilidad del mercado
4. **Correlation Risk**: Correlación entre activos
5. **Drawdown Risk**: Pérdidas acumuladas

### Implementación de Stop-Loss Dinámico

```python
def calculate_dynamic_stop_loss(entry_price, volatility, confidence):
    base_stop = 0.02  # 2% base
    volatility_adjustment = volatility * 0.5
    confidence_adjustment = (1 - confidence) * 0.01
    
    dynamic_stop = base_stop + volatility_adjustment + confidence_adjustment
    return entry_price * (1 - dynamic_stop)
```

---

## 📱 Dashboard y Monitoreo

### Streamlit Dashboard (`dashboard/streamlit_app/app.py`)

**Características:**
- **Vista en Tiempo Real**: Precios, volumen, indicadores
- **Gestión de Agentes**: Estado, métricas, configuración
- **Análisis de Rendimiento**: Gráficos, métricas, trades
- **Señales de Trading**: Historial y análisis
- **Configuración**: Parámetros del sistema

### Ejecutar Dashboard

```bash
# Método 1: Integrado con main.py
python main.py

# Método 2: Standalone
streamlit run dashboard/streamlit_app/app.py --server.port 8501
```

### Métricas en Tiempo Real

- **Precio Actual**: Último precio del activo
- **PnL Diario**: Ganancia/pérdida del día
- **Posiciones Activas**: Estado de posiciones abiertas
- **Órdenes Pendientes**: Órdenes no ejecutadas
- **Riesgo del Portafolio**: Nivel de riesgo actual

---

## 🚀 Deployment

### Docker Deployment

```bash
# Construir imagen
docker build -t ai-trading-system .

# Ejecutar con docker-compose
docker-compose up -d

# Verificar servicios
docker-compose ps
```

### Servicios Incluidos

- **ai-trading-system**: Aplicación principal
- **postgres**: Base de datos
- **redis**: Cache y real-time data
- **prometheus**: Métricas
- **grafana**: Visualización
- **jupyter**: Análisis y desarrollo

### Configuración de Producción

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  ai-trading-system:
    environment:
      - ENVIRONMENT=production
      - TRADING_MODE=live  # ⚠️ Solo cuando esté listo
      - DEBUG=false
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

### Monitoreo en Producción

- **Prometheus**: Métricas del sistema
- **Grafana**: Dashboards visuales
- **Logs estructurados**: JSON logging
- **Alertas**: Telegram/Discord/Email

---

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión con Exchange

```bash
# Verificar API keys
python -c "from utils.config.settings import settings; print(settings.BINANCE_API_KEY[:10])"

# Probar conexión
python -c "import ccxt; exchange = ccxt.binance({'apiKey': 'key', 'secret': 'secret', 'sandbox': True}); print(exchange.fetch_balance())"
```

#### 2. Problemas de Dependencias

```bash
# Reinstalar dependencias
pip install --upgrade -r requirements.txt

# Verificar versiones
pip list | grep -E "(pandas|numpy|ccxt)"
```

#### 3. Errores de Base de Datos

```bash
# Verificar conexión PostgreSQL
docker-compose exec postgres psql -U trading_user -d trading_db -c "SELECT version();"

# Reiniciar servicios
docker-compose restart postgres redis
```

#### 4. Problemas de Memoria

```bash
# Monitorear uso de memoria
docker stats

# Ajustar límites en docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

### Logs y Debugging

```bash
# Ver logs de la aplicación
docker-compose logs -f ai-trading-system

# Logs específicos de trading
tail -f logs/trading.log

# Logs estructurados
grep "trade_signal" logs/trading.log | jq .
```

### Performance Tuning

1. **Optimizar Cache**: Ajustar TTL de Redis
2. **Batch Processing**: Procesar múltiples señales juntas
3. **Async Operations**: Usar asyncio para I/O
4. **Database Indexing**: Índices en columnas frecuentes

---

## 📚 Recursos Adicionales

### Documentación de APIs

- [Binance API](https://binance-docs.github.io/apidocs/)
- [CCXT Documentation](https://docs.ccxt.com/)
- [Pandas TA](https://github.com/twopirllc/pandas-ta)

### Libros Recomendados

- "Algorithmic Trading" by Ernie Chan
- "Quantitative Trading" by Ernie Chan
- "Machine Learning for Asset Managers" by Marcos López de Prado

### Comunidades

- [QuantConnect Community](https://www.quantconnect.com/forum)
- [Algorithmic Trading Reddit](https://reddit.com/r/algotrading)
- [Python for Finance](https://github.com/yhilpisch/py4fi2nd)

---

## ⚠️ Disclaimers Importantes

1. **Riesgo Financiero**: El trading conlleva riesgos significativos
2. **Paper Trading Primero**: Siempre probar en simulación
3. **No Garantías**: Rendimientos pasados no garantizan futuros
4. **Responsabilidad**: Usar bajo tu propia responsabilidad
5. **Regulaciones**: Cumplir con regulaciones locales

---

## 🤝 Contribución

### Cómo Contribuir

1. Fork del repositorio
2. Crear branch para feature (`git checkout -b feature/nueva-estrategia`)
3. Commit cambios (`git commit -am 'Agregar nueva estrategia'`)
4. Push al branch (`git push origin feature/nueva-estrategia`)
5. Crear Pull Request

### Estándares de Código

- **PEP 8**: Estilo de código Python
- **Type Hints**: Usar anotaciones de tipo
- **Docstrings**: Documentar funciones y clases
- **Tests**: Incluir tests para nuevas funcionalidades

---

**🎉 ¡Gracias por usar AI Trading System!**

Para soporte técnico, crear un issue en GitHub o contactar al equipo de desarrollo.

---

*Última actualización: Noviembre 2025*