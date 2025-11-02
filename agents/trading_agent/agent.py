"""
🤖 Trading Agent - Agente IA de Trading

Agente autónomo que ejecuta estrategias de trading basado en análisis
técnico, machine learning y gestión de riesgo inteligente.
"""

import asyncio
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from data.feeds.market_data import MarketDataManager
from strategies.technical.indicators import (
    MultiIndicatorStrategy, RSIStrategy, MACDStrategy, 
    TradingSignal, SignalType
)
from backtesting.engine.backtest_engine import BacktestEngine
from utils.config.settings import Settings
from utils.logging.logger import trading_logger


@dataclass
class AgentState:
    """Estado del agente de trading."""
    is_running: bool = False
    last_update: Optional[datetime] = None
    current_positions: Dict[str, float] = None
    performance_metrics: Dict[str, float] = None
    active_strategies: List[str] = None
    
    def __post_init__(self):
        if self.current_positions is None:
            self.current_positions = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.active_strategies is None:
            self.active_strategies = []


@dataclass
class TradingDecision:
    """Decisión de trading del agente."""
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0.0 a 1.0
    quantity: float
    reasoning: str
    supporting_signals: List[TradingSignal]
    risk_assessment: Dict[str, float]
    timestamp: datetime


class TradingAgent:
    """Agente IA principal de trading."""
    
    def __init__(
        self, 
        market_data: MarketDataManager,
        settings: Settings,
        agent_id: str = "trading_agent_001"
    ):
        self.agent_id = agent_id
        self.market_data = market_data
        self.settings = settings
        self.state = AgentState()
        
        # Estrategias disponibles
        self.strategies = {
            'rsi': RSIStrategy(),
            'macd': MACDStrategy(),
            'multi': MultiIndicatorStrategy()
        }
        
        # Motor de backtesting para validación
        self.backtest_engine = BacktestEngine(
            initial_capital=self.settings.BACKTEST_INITIAL_CAPITAL,
            commission_rate=0.001,
            max_position_size=self.settings.MAX_POSITION_SIZE
        )
        
        # Historial de decisiones
        self.decision_history: List[TradingDecision] = []
        
        # Configuración de riesgo
        self.risk_config = {
            'max_position_size': self.settings.MAX_POSITION_SIZE,
            'max_daily_loss': self.settings.MAX_DAILY_LOSS,
            'stop_loss_percent': self.settings.STOP_LOSS_PERCENT,
            'take_profit_percent': self.settings.TAKE_PROFIT_PERCENT
        }
    
    async def initialize(self):
        """Inicializar el agente."""
        trading_logger.logger.info(f"🤖 Inicializando Trading Agent {self.agent_id}")
        
        # Validar configuración
        config_errors = self.settings.validate_trading_config()
        if config_errors:
            for error in config_errors:
                trading_logger.logger.error(f"❌ Error de configuración: {error}")
            raise ValueError("Configuración inválida")
        
        # Inicializar estrategias activas
        self.state.active_strategies = ['multi']  # Empezar con estrategia multi-indicador
        
        # Cargar estado previo si existe
        await self._load_agent_state()
        
        self.state.is_running = True
        self.state.last_update = datetime.now()
        
        trading_logger.agent_action(
            agent_name=self.agent_id,
            action="initialize",
            result="success"
        )
    
    async def run(self):
        """Ejecutar el bucle principal del agente."""
        if not self.state.is_running:
            await self.initialize()
        
        trading_logger.logger.info(f"🚀 Trading Agent {self.agent_id} iniciado")
        
        try:
            while self.state.is_running:
                await self._trading_cycle()
                await asyncio.sleep(self.settings.AGENT_UPDATE_INTERVAL)
                
        except Exception as e:
            trading_logger.logger.error(f"❌ Error en Trading Agent: {e}")
            raise
        finally:
            await self._save_agent_state()
    
    async def _trading_cycle(self):
        """Ciclo principal de trading."""
        try:
            # 1. Obtener datos de mercado
            market_data = await self._get_market_data()
            if market_data.empty:
                trading_logger.logger.warning("⚠️ No hay datos de mercado disponibles")
                return
            
            # 2. Analizar mercado con estrategias activas
            signals = await self._analyze_market(market_data)
            
            # 3. Evaluar riesgo
            risk_assessment = await self._assess_risk(signals, market_data)
            
            # 4. Tomar decisión de trading
            decision = await self._make_trading_decision(signals, risk_assessment)
            
            # 5. Ejecutar decisión (solo en paper trading por ahora)
            if decision and decision.action != 'hold':
                await self._execute_decision(decision)
            
            # 6. Actualizar métricas de rendimiento
            await self._update_performance_metrics()
            
            # 7. Guardar estado
            self.state.last_update = datetime.now()
            
            trading_logger.agent_action(
                agent_name=self.agent_id,
                action="trading_cycle",
                result="completed",
                decision=decision.action if decision else "no_decision"
            )
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error en ciclo de trading: {e}")
    
    async def _get_market_data(self) -> pd.DataFrame:
        """Obtener datos de mercado actuales."""
        symbol = self.settings.DEFAULT_SYMBOL
        
        # Obtener datos OHLCV recientes
        ohlcv_data = await self.market_data.get_ohlcv(
            symbol=symbol,
            timeframe='1h',
            limit=200  # Suficientes datos para indicadores
        )
        
        if not ohlcv_data:
            return pd.DataFrame()
        
        # Convertir a DataFrame
        data = []
        for candle in ohlcv_data:
            data.append({
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        return df
    
    async def _analyze_market(self, market_data: pd.DataFrame) -> List[TradingSignal]:
        """Analizar mercado con estrategias activas."""
        signals = []
        
        for strategy_name in self.state.active_strategies:
            if strategy_name in self.strategies:
                strategy = self.strategies[strategy_name]
                signal = strategy.analyze(market_data)
                
                if signal:
                    signals.append(signal)
                    
                    trading_logger.trade_signal(
                        symbol=self.settings.DEFAULT_SYMBOL,
                        action=signal.signal.value,
                        price=signal.price,
                        reason=f"{strategy_name}: {signal.reason}"
                    )
        
        return signals
    
    async def _assess_risk(
        self, 
        signals: List[TradingSignal], 
        market_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Evaluar riesgo de las señales."""
        if not signals:
            return {'overall_risk': 0.0}
        
        # Calcular volatilidad reciente
        returns = market_data['close'].pct_change().dropna()
        volatility = returns.std() * 100  # Volatilidad en %
        
        # Evaluar consistencia de señales
        buy_signals = sum(1 for s in signals if s.signal == SignalType.BUY)
        sell_signals = sum(1 for s in signals if s.signal == SignalType.SELL)
        signal_consistency = abs(buy_signals - sell_signals) / len(signals)
        
        # Evaluar fuerza promedio de señales
        avg_strength = sum(s.strength for s in signals) / len(signals)
        
        # Calcular riesgo general
        volatility_risk = min(volatility / 5.0, 1.0)  # Normalizar volatilidad
        consistency_risk = 1.0 - signal_consistency
        strength_risk = 1.0 - avg_strength
        
        overall_risk = (volatility_risk + consistency_risk + strength_risk) / 3
        
        risk_assessment = {
            'overall_risk': overall_risk,
            'volatility_risk': volatility_risk,
            'consistency_risk': consistency_risk,
            'strength_risk': strength_risk,
            'volatility': volatility,
            'signal_consistency': signal_consistency,
            'avg_strength': avg_strength
        }
        
        # Log de evaluación de riesgo
        if overall_risk > 0.7:
            trading_logger.risk_alert(
                message=f"Alto riesgo detectado: {overall_risk:.2f}",
                severity="high",
                **risk_assessment
            )
        
        return risk_assessment
    
    async def _make_trading_decision(
        self, 
        signals: List[TradingSignal], 
        risk_assessment: Dict[str, float]
    ) -> Optional[TradingDecision]:
        """Tomar decisión de trading basada en señales y riesgo."""
        if not signals:
            return None
        
        # Filtrar por riesgo
        if risk_assessment['overall_risk'] > 0.8:
            trading_logger.logger.warning("⚠️ Riesgo muy alto, evitando trading")
            return None
        
        # Agregar señales
        buy_votes = 0
        sell_votes = 0
        total_confidence = 0
        
        for signal in signals:
            if signal.signal == SignalType.BUY:
                buy_votes += signal.strength
            elif signal.signal == SignalType.SELL:
                sell_votes += signal.strength
            
            total_confidence += signal.strength
        
        # Determinar acción
        if buy_votes > sell_votes and buy_votes > 0.5:
            action = 'buy'
            confidence = buy_votes / len(signals)
        elif sell_votes > buy_votes and sell_votes > 0.5:
            action = 'sell'
            confidence = sell_votes / len(signals)
        else:
            action = 'hold'
            confidence = 0.0
        
        # Ajustar confianza por riesgo
        confidence *= (1.0 - risk_assessment['overall_risk'])
        
        # Calcular cantidad
        if action != 'hold':
            quantity = self._calculate_position_size(confidence, risk_assessment)
        else:
            quantity = 0.0
        
        # Crear decisión
        decision = TradingDecision(
            symbol=self.settings.DEFAULT_SYMBOL,
            action=action,
            confidence=confidence,
            quantity=quantity,
            reasoning=self._generate_reasoning(signals, risk_assessment, action),
            supporting_signals=signals,
            risk_assessment=risk_assessment,
            timestamp=datetime.now()
        )
        
        # Guardar en historial
        self.decision_history.append(decision)
        
        # Mantener solo las últimas 1000 decisiones
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]
        
        return decision
    
    def _calculate_position_size(
        self, 
        confidence: float, 
        risk_assessment: Dict[str, float]
    ) -> float:
        """Calcular tamaño de posición basado en confianza y riesgo."""
        # Tamaño base basado en confianza
        base_size = confidence * self.risk_config['max_position_size']
        
        # Ajustar por riesgo
        risk_multiplier = 1.0 - risk_assessment['overall_risk']
        adjusted_size = base_size * risk_multiplier
        
        # Aplicar límites mínimos y máximos
        min_size = 0.01  # 1% mínimo
        max_size = self.risk_config['max_position_size']
        
        return max(min_size, min(adjusted_size, max_size))
    
    def _generate_reasoning(
        self, 
        signals: List[TradingSignal], 
        risk_assessment: Dict[str, float], 
        action: str
    ) -> str:
        """Generar explicación de la decisión."""
        reasoning_parts = []
        
        # Resumen de señales
        buy_count = sum(1 for s in signals if s.signal == SignalType.BUY)
        sell_count = sum(1 for s in signals if s.signal == SignalType.SELL)
        
        reasoning_parts.append(f"Señales: {buy_count} compra, {sell_count} venta")
        
        # Evaluación de riesgo
        risk_level = "bajo" if risk_assessment['overall_risk'] < 0.3 else \
                    "medio" if risk_assessment['overall_risk'] < 0.7 else "alto"
        reasoning_parts.append(f"Riesgo {risk_level} ({risk_assessment['overall_risk']:.2f})")
        
        # Volatilidad
        reasoning_parts.append(f"Volatilidad: {risk_assessment['volatility']:.2f}%")
        
        # Acción tomada
        reasoning_parts.append(f"Acción: {action}")
        
        return " | ".join(reasoning_parts)
    
    async def _execute_decision(self, decision: TradingDecision):
        """Ejecutar decisión de trading."""
        if self.settings.TRADING_MODE == "paper":
            # Paper trading - solo logging
            trading_logger.trade_executed(
                symbol=decision.symbol,
                action=decision.action,
                quantity=decision.quantity,
                price=decision.supporting_signals[0].price if decision.supporting_signals else 0.0,
                order_id=f"paper_{datetime.now().timestamp()}"
            )
            
            trading_logger.logger.info(
                f"📝 Paper Trade: {decision.action.upper()} {decision.quantity:.4f} "
                f"{decision.symbol} - Confianza: {decision.confidence:.2f}"
            )
        
        else:
            # Trading real - implementar conexión con exchange
            trading_logger.logger.warning("⚠️ Trading real no implementado aún")
    
    async def _update_performance_metrics(self):
        """Actualizar métricas de rendimiento."""
        if len(self.decision_history) < 10:
            return
        
        # Calcular métricas básicas
        recent_decisions = self.decision_history[-100:]  # Últimas 100 decisiones
        
        buy_decisions = [d for d in recent_decisions if d.action == 'buy']
        sell_decisions = [d for d in recent_decisions if d.action == 'sell']
        
        avg_confidence = sum(d.confidence for d in recent_decisions) / len(recent_decisions)
        avg_risk = sum(d.risk_assessment['overall_risk'] for d in recent_decisions) / len(recent_decisions)
        
        self.state.performance_metrics = {
            'total_decisions': len(self.decision_history),
            'recent_decisions': len(recent_decisions),
            'buy_decisions': len(buy_decisions),
            'sell_decisions': len(sell_decisions),
            'avg_confidence': avg_confidence,
            'avg_risk': avg_risk,
            'last_update': datetime.now().isoformat()
        }
        
        # Log métricas
        trading_logger.performance_metric(
            metric_name="avg_confidence",
            value=avg_confidence,
            agent=self.agent_id
        )
        
        trading_logger.performance_metric(
            metric_name="avg_risk",
            value=avg_risk,
            agent=self.agent_id
        )
    
    async def _load_agent_state(self):
        """Cargar estado previo del agente."""
        # Implementar carga desde base de datos o archivo
        # Por ahora, usar valores por defecto
        pass
    
    async def _save_agent_state(self):
        """Guardar estado del agente."""
        # Implementar guardado en base de datos o archivo
        state_data = {
            'agent_id': self.agent_id,
            'state': {
                'is_running': self.state.is_running,
                'last_update': self.state.last_update.isoformat() if self.state.last_update else None,
                'current_positions': self.state.current_positions,
                'performance_metrics': self.state.performance_metrics,
                'active_strategies': self.state.active_strategies
            },
            'decision_count': len(self.decision_history)
        }
        
        # Por ahora, solo log
        trading_logger.logger.debug(f"💾 Estado del agente guardado: {json.dumps(state_data, indent=2)}")
    
    async def stop(self):
        """Detener el agente."""
        trading_logger.logger.info(f"🛑 Deteniendo Trading Agent {self.agent_id}")
        
        self.state.is_running = False
        await self._save_agent_state()
        
        trading_logger.agent_action(
            agent_name=self.agent_id,
            action="stop",
            result="success"
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del agente."""
        return {
            'agent_id': self.agent_id,
            'is_running': self.state.is_running,
            'last_update': self.state.last_update.isoformat() if self.state.last_update else None,
            'active_strategies': self.state.active_strategies,
            'performance_metrics': self.state.performance_metrics,
            'total_decisions': len(self.decision_history),
            'recent_decisions': len([d for d in self.decision_history if d.timestamp > datetime.now() - timedelta(hours=24)])
        }