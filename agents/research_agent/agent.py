"""
🔬 Research Agent - Agente de Investigación IA

Agente especializado en descubrir y validar nuevas estrategias de trading
mediante análisis de patrones, backtesting automático y optimización.
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import itertools

from data.feeds.market_data import MarketDataManager
from strategies.technical.indicators import (
    RSIStrategy, MACDStrategy, BollingerBandsStrategy,
    TechnicalIndicators, TradingStrategy, TradingSignal, SignalType
)
from backtesting.engine.backtest_engine import BacktestEngine
from utils.config.settings import Settings
from utils.logging.logger import trading_logger


@dataclass
class StrategyCandidate:
    """Candidato de estrategia para investigación."""
    name: str
    strategy: TradingStrategy
    parameters: Dict[str, Any]
    backtest_results: Optional[Dict[str, Any]] = None
    fitness_score: float = 0.0
    validation_score: float = 0.0
    risk_score: float = 0.0


@dataclass
class ResearchResult:
    """Resultado de investigación."""
    timestamp: datetime
    best_strategies: List[StrategyCandidate]
    total_tested: int
    success_rate: float
    avg_fitness: float
    research_duration: timedelta
    recommendations: List[str]


class ResearchAgent:
    """Agente de investigación de estrategias."""
    
    def __init__(
        self,
        market_data: MarketDataManager,
        settings: Settings,
        agent_id: str = "research_agent_001"
    ):
        self.agent_id = agent_id
        self.market_data = market_data
        self.settings = settings
        
        # Motor de backtesting
        self.backtest_engine = BacktestEngine(
            initial_capital=self.settings.BACKTEST_INITIAL_CAPITAL,
            commission_rate=0.001,
            max_position_size=0.8
        )
        
        # Estado del agente
        self.is_running = False
        self.research_history: List[ResearchResult] = []
        self.best_strategies: List[StrategyCandidate] = []
        
        # Configuración de investigación
        self.research_config = {
            'max_strategies_per_cycle': 20,
            'min_fitness_threshold': 0.6,
            'validation_split': 0.3,
            'optimization_iterations': 50
        }
    
    async def initialize(self):
        """Inicializar el agente de investigación."""
        trading_logger.logger.info(f"🔬 Inicializando Research Agent {self.agent_id}")
        
        self.is_running = True
        
        trading_logger.agent_action(
            agent_name=self.agent_id,
            action="initialize",
            result="success"
        )
    
    async def run_research_cycle(self) -> ResearchResult:
        """Ejecutar un ciclo completo de investigación."""
        start_time = datetime.now()
        trading_logger.logger.info("🔍 Iniciando ciclo de investigación...")
        
        try:
            # 1. Obtener datos históricos
            historical_data = await self._get_research_data()
            if historical_data.empty:
                raise ValueError("No hay datos suficientes para investigación")
            
            # 2. Generar candidatos de estrategias
            candidates = await self._generate_strategy_candidates()
            trading_logger.logger.info(f"📊 Generados {len(candidates)} candidatos de estrategias")
            
            # 3. Dividir datos para entrenamiento y validación
            train_data, validation_data = self._split_data(historical_data)
            
            # 4. Evaluar candidatos
            evaluated_candidates = []
            for i, candidate in enumerate(candidates):
                trading_logger.logger.info(f"🧪 Evaluando candidato {i+1}/{len(candidates)}: {candidate.name}")
                
                # Backtest en datos de entrenamiento
                train_results = await self._evaluate_candidate(candidate, train_data)
                candidate.backtest_results = train_results
                candidate.fitness_score = self._calculate_fitness_score(train_results)
                
                # Validación en datos separados
                validation_results = await self._evaluate_candidate(candidate, validation_data)
                candidate.validation_score = self._calculate_fitness_score(validation_results)
                candidate.risk_score = self._calculate_risk_score(train_results)
                
                evaluated_candidates.append(candidate)
            
            # 5. Seleccionar mejores estrategias
            best_candidates = self._select_best_strategies(evaluated_candidates)
            
            # 6. Generar recomendaciones
            recommendations = self._generate_recommendations(best_candidates, evaluated_candidates)
            
            # 7. Crear resultado de investigación
            end_time = datetime.now()
            research_result = ResearchResult(
                timestamp=start_time,
                best_strategies=best_candidates,
                total_tested=len(candidates),
                success_rate=len(best_candidates) / len(candidates) if candidates else 0,
                avg_fitness=np.mean([c.fitness_score for c in evaluated_candidates]) if evaluated_candidates else 0,
                research_duration=end_time - start_time,
                recommendations=recommendations
            )
            
            # 8. Guardar resultados
            self.research_history.append(research_result)
            self.best_strategies = best_candidates
            
            trading_logger.logger.info(f"✅ Investigación completada en {research_result.research_duration}")
            trading_logger.logger.info(f"🏆 Encontradas {len(best_candidates)} estrategias prometedoras")
            
            return research_result
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error en ciclo de investigación: {e}")
            raise
    
    async def _get_research_data(self) -> pd.DataFrame:
        """Obtener datos históricos para investigación."""
        symbol = self.settings.DEFAULT_SYMBOL
        
        # Obtener 6 meses de datos horarios
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        historical_data = await self.market_data.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe='1h'
        )
        
        return historical_data
    
    async def _generate_strategy_candidates(self) -> List[StrategyCandidate]:
        """Generar candidatos de estrategias con diferentes parámetros."""
        candidates = []
        
        # RSI Strategy variants
        rsi_params = [
            {'rsi_period': 14, 'oversold_threshold': 30, 'overbought_threshold': 70},
            {'rsi_period': 14, 'oversold_threshold': 25, 'overbought_threshold': 75},
            {'rsi_period': 21, 'oversold_threshold': 30, 'overbought_threshold': 70},
            {'rsi_period': 7, 'oversold_threshold': 20, 'overbought_threshold': 80},
        ]
        
        for i, params in enumerate(rsi_params):
            strategy = RSIStrategy(**params)
            candidate = StrategyCandidate(
                name=f"RSI_v{i+1}",
                strategy=strategy,
                parameters=params
            )
            candidates.append(candidate)
        
        # MACD Strategy variants
        macd_params = [
            {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
            {'fast_period': 8, 'slow_period': 21, 'signal_period': 5},
            {'fast_period': 5, 'slow_period': 13, 'signal_period': 8},
            {'fast_period': 19, 'slow_period': 39, 'signal_period': 9},
        ]
        
        for i, params in enumerate(macd_params):
            strategy = MACDStrategy(**params)
            candidate = StrategyCandidate(
                name=f"MACD_v{i+1}",
                strategy=strategy,
                parameters=params
            )
            candidates.append(candidate)
        
        # Bollinger Bands variants
        bb_params = [
            {'period': 20, 'std_dev': 2.0},
            {'period': 20, 'std_dev': 1.5},
            {'period': 14, 'std_dev': 2.0},
            {'period': 28, 'std_dev': 2.5},
        ]
        
        for i, params in enumerate(bb_params):
            strategy = BollingerBandsStrategy(**params)
            candidate = StrategyCandidate(
                name=f"BB_v{i+1}",
                strategy=strategy,
                parameters=params
            )
            candidates.append(candidate)
        
        # Estrategias híbridas (combinaciones)
        hybrid_candidates = await self._generate_hybrid_strategies()
        candidates.extend(hybrid_candidates)
        
        return candidates[:self.research_config['max_strategies_per_cycle']]
    
    async def _generate_hybrid_strategies(self) -> List[StrategyCandidate]:
        """Generar estrategias híbridas combinando indicadores."""
        candidates = []
        
        # Ejemplo de estrategia híbrida RSI + MACD
        class RSI_MACD_Hybrid(TradingStrategy):
            def __init__(self, rsi_period=14, rsi_oversold=30, rsi_overbought=70,
                        macd_fast=12, macd_slow=26, macd_signal=9):
                super().__init__("RSI_MACD_Hybrid")
                self.rsi_period = rsi_period
                self.rsi_oversold = rsi_oversold
                self.rsi_overbought = rsi_overbought
                self.macd_fast = macd_fast
                self.macd_slow = macd_slow
                self.macd_signal = macd_signal
            
            def analyze(self, df):
                if len(df) < max(self.macd_slow, self.rsi_period) + 10:
                    return None
                
                # Calcular RSI
                rsi = self.indicators.rsi(df['close'], self.rsi_period)
                current_rsi = rsi.iloc[-1]
                
                # Calcular MACD
                macd, signal, histogram = self.indicators.macd(
                    df['close'], self.macd_fast, self.macd_slow, self.macd_signal
                )
                current_histogram = histogram.iloc[-1]
                prev_histogram = histogram.iloc[-2]
                
                current_price = df['close'].iloc[-1]
                current_time = df.index[-1]
                
                # Lógica híbrida
                rsi_signal = None
                if current_rsi < self.rsi_oversold:
                    rsi_signal = SignalType.BUY
                elif current_rsi > self.rsi_overbought:
                    rsi_signal = SignalType.SELL
                
                macd_signal_type = None
                if prev_histogram < 0 and current_histogram > 0:
                    macd_signal_type = SignalType.BUY
                elif prev_histogram > 0 and current_histogram < 0:
                    macd_signal_type = SignalType.SELL
                
                # Combinar señales
                if rsi_signal == macd_signal_type and rsi_signal is not None:
                    # Ambos indicadores coinciden
                    strength = 0.8
                    final_signal = rsi_signal
                    reason = f"RSI + MACD {final_signal.value}"
                elif rsi_signal is not None and macd_signal_type is None:
                    # Solo RSI
                    strength = 0.5
                    final_signal = rsi_signal
                    reason = f"RSI {final_signal.value}"
                elif macd_signal_type is not None and rsi_signal is None:
                    # Solo MACD
                    strength = 0.5
                    final_signal = macd_signal_type
                    reason = f"MACD {final_signal.value}"
                else:
                    # Sin señal o señales contradictorias
                    strength = 0.0
                    final_signal = SignalType.HOLD
                    reason = "No signal or conflicting signals"
                
                return TradingSignal(
                    signal=final_signal,
                    strength=strength,
                    price=current_price,
                    timestamp=current_time,
                    reason=reason,
                    indicators={
                        "rsi": current_rsi,
                        "macd_histogram": current_histogram
                    }
                )
        
        # Crear variantes de la estrategia híbrida
        hybrid_params = [
            {'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70},
            {'rsi_period': 21, 'rsi_oversold': 25, 'rsi_overbought': 75},
        ]
        
        for i, params in enumerate(hybrid_params):
            strategy = RSI_MACD_Hybrid(**params)
            candidate = StrategyCandidate(
                name=f"RSI_MACD_Hybrid_v{i+1}",
                strategy=strategy,
                parameters=params
            )
            candidates.append(candidate)
        
        return candidates
    
    def _split_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Dividir datos en entrenamiento y validación."""
        split_point = int(len(data) * (1 - self.research_config['validation_split']))
        
        train_data = data.iloc[:split_point].copy()
        validation_data = data.iloc[split_point:].copy()
        
        return train_data, validation_data
    
    async def _evaluate_candidate(
        self, 
        candidate: StrategyCandidate, 
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Evaluar un candidato de estrategia."""
        try:
            results = self.backtest_engine.run_backtest(
                strategy=candidate.strategy,
                data=data,
                symbol=self.settings.DEFAULT_SYMBOL
            )
            return results
        except Exception as e:
            trading_logger.logger.error(f"❌ Error evaluando {candidate.name}: {e}")
            return {
                'total_return': -100,
                'total_trades': 0,
                'win_rate': 0,
                'sharpe_ratio': -10,
                'max_drawdown': 100
            }
    
    def _calculate_fitness_score(self, results: Dict[str, Any]) -> float:
        """Calcular score de fitness para una estrategia."""
        if results['total_trades'] == 0:
            return 0.0
        
        # Componentes del fitness score
        return_score = min(results['total_return'] / 100, 1.0)  # Normalizar a [0,1]
        win_rate_score = results['win_rate'] / 100
        sharpe_score = min(max(results['sharpe_ratio'] / 3, 0), 1.0)  # Normalizar Sharpe
        drawdown_penalty = max(0, 1 - results['max_drawdown'] / 50)  # Penalizar drawdown alto
        
        # Peso de cada componente
        weights = {
            'return': 0.3,
            'win_rate': 0.2,
            'sharpe': 0.3,
            'drawdown': 0.2
        }
        
        fitness_score = (
            return_score * weights['return'] +
            win_rate_score * weights['win_rate'] +
            sharpe_score * weights['sharpe'] +
            drawdown_penalty * weights['drawdown']
        )
        
        return max(0, min(fitness_score, 1.0))
    
    def _calculate_risk_score(self, results: Dict[str, Any]) -> float:
        """Calcular score de riesgo (0 = bajo riesgo, 1 = alto riesgo)."""
        if results['total_trades'] == 0:
            return 1.0
        
        # Factores de riesgo
        drawdown_risk = min(results['max_drawdown'] / 50, 1.0)
        volatility_risk = max(0, 1 - results['sharpe_ratio'] / 2) if results['sharpe_ratio'] > 0 else 1.0
        consistency_risk = 1 - (results['win_rate'] / 100)
        
        # Promedio ponderado
        risk_score = (drawdown_risk * 0.4 + volatility_risk * 0.3 + consistency_risk * 0.3)
        
        return max(0, min(risk_score, 1.0))
    
    def _select_best_strategies(self, candidates: List[StrategyCandidate]) -> List[StrategyCandidate]:
        """Seleccionar las mejores estrategias basado en múltiples criterios."""
        # Filtrar por fitness mínimo
        qualified_candidates = [
            c for c in candidates 
            if c.fitness_score >= self.research_config['min_fitness_threshold']
        ]
        
        if not qualified_candidates:
            # Si ninguno califica, tomar los mejores 3
            qualified_candidates = sorted(candidates, key=lambda x: x.fitness_score, reverse=True)[:3]
        
        # Ordenar por score combinado (fitness - risk)
        def combined_score(candidate):
            return candidate.fitness_score * 0.7 + (1 - candidate.risk_score) * 0.3
        
        best_strategies = sorted(qualified_candidates, key=combined_score, reverse=True)
        
        # Tomar top 5
        return best_strategies[:5]
    
    def _generate_recommendations(
        self, 
        best_strategies: List[StrategyCandidate],
        all_candidates: List[StrategyCandidate]
    ) -> List[str]:
        """Generar recomendaciones basadas en los resultados."""
        recommendations = []
        
        if not best_strategies:
            recommendations.append("❌ No se encontraron estrategias prometedoras")
            recommendations.append("💡 Considerar ajustar parámetros de búsqueda")
            return recommendations
        
        # Mejor estrategia
        best = best_strategies[0]
        recommendations.append(f"🏆 Mejor estrategia: {best.name} (Fitness: {best.fitness_score:.2f})")
        
        # Análisis de rendimiento
        if best.backtest_results:
            results = best.backtest_results
            recommendations.append(f"📈 Rendimiento: {results['total_return']:.1f}%")
            recommendations.append(f"🎯 Win Rate: {results['win_rate']:.1f}%")
            recommendations.append(f"📊 Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        
        # Análisis de riesgo
        if best.risk_score < 0.3:
            recommendations.append("✅ Riesgo bajo - Estrategia conservadora")
        elif best.risk_score < 0.6:
            recommendations.append("⚠️ Riesgo medio - Monitorear de cerca")
        else:
            recommendations.append("🚨 Riesgo alto - Usar con precaución")
        
        # Diversificación
        strategy_types = set(c.name.split('_')[0] for c in best_strategies)
        if len(strategy_types) > 1:
            recommendations.append("🔄 Buena diversificación de estrategias encontrada")
        else:
            recommendations.append("💡 Considerar diversificar tipos de estrategias")
        
        # Consistencia
        fitness_scores = [c.fitness_score for c in best_strategies]
        if len(fitness_scores) > 1 and np.std(fitness_scores) < 0.1:
            recommendations.append("📊 Estrategias con rendimiento consistente")
        
        return recommendations
    
    async def get_research_summary(self) -> Dict[str, Any]:
        """Obtener resumen de investigación."""
        if not self.research_history:
            return {"message": "No hay historial de investigación disponible"}
        
        latest_research = self.research_history[-1]
        
        return {
            "agent_id": self.agent_id,
            "last_research": latest_research.timestamp.isoformat(),
            "total_research_cycles": len(self.research_history),
            "best_strategies_count": len(self.best_strategies),
            "latest_success_rate": latest_research.success_rate,
            "latest_avg_fitness": latest_research.avg_fitness,
            "best_strategies": [
                {
                    "name": s.name,
                    "fitness_score": s.fitness_score,
                    "risk_score": s.risk_score,
                    "parameters": s.parameters
                }
                for s in self.best_strategies
            ],
            "recommendations": latest_research.recommendations
        }
    
    async def stop(self):
        """Detener el agente de investigación."""
        trading_logger.logger.info(f"🛑 Deteniendo Research Agent {self.agent_id}")
        self.is_running = False
        
        trading_logger.agent_action(
            agent_name=self.agent_id,
            action="stop",
            result="success"
        )