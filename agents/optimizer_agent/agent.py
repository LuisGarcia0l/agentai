"""
⚡ Optimizer Agent - Agente de Optimización IA

Agente especializado en optimizar parámetros de estrategias existentes
usando algoritmos genéticos, grid search y optimización bayesiana.
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import random
from itertools import product

from data.feeds.market_data import MarketDataManager
from strategies.technical.indicators import RSIStrategy, MACDStrategy, TradingStrategy
from backtesting.engine.backtest_engine import BacktestEngine
from utils.config.settings import Settings
from utils.logging.logger import trading_logger


@dataclass
class OptimizationParameter:
    """Parámetro para optimización."""
    name: str
    min_value: float
    max_value: float
    step: float
    current_value: float
    parameter_type: str = "float"  # float, int, bool


@dataclass
class OptimizationResult:
    """Resultado de optimización."""
    parameters: Dict[str, Any]
    fitness_score: float
    backtest_results: Dict[str, Any]
    validation_score: float
    generation: int = 0


@dataclass
class OptimizationSummary:
    """Resumen de optimización."""
    strategy_name: str
    optimization_method: str
    start_time: datetime
    end_time: datetime
    total_iterations: int
    best_result: OptimizationResult
    improvement_percentage: float
    convergence_generation: int
    final_recommendations: List[str]


class OptimizerAgent:
    """Agente de optimización de estrategias."""
    
    def __init__(
        self,
        market_data: MarketDataManager,
        settings: Settings,
        agent_id: str = "optimizer_agent_001"
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
        self.optimization_history: List[OptimizationSummary] = []
        self.current_optimization: Optional[OptimizationSummary] = None
        
        # Configuración de optimización
        self.optimization_config = {
            'genetic_algorithm': {
                'population_size': 20,
                'generations': 30,
                'mutation_rate': 0.1,
                'crossover_rate': 0.8,
                'elite_size': 2
            },
            'grid_search': {
                'max_combinations': 100
            },
            'bayesian': {
                'n_calls': 50,
                'n_initial_points': 10
            }
        }
    
    async def initialize(self):
        """Inicializar el agente de optimización."""
        trading_logger.logger.info(f"⚡ Inicializando Optimizer Agent {self.agent_id}")
        
        self.is_running = True
        
        trading_logger.agent_action(
            agent_name=self.agent_id,
            action="initialize",
            result="success"
        )
    
    async def optimize_strategy(
        self,
        strategy_class: type,
        base_parameters: Dict[str, Any],
        optimization_parameters: List[OptimizationParameter],
        method: str = "genetic_algorithm"
    ) -> OptimizationSummary:
        """
        Optimizar una estrategia usando el método especificado.
        
        Args:
            strategy_class: Clase de la estrategia a optimizar
            base_parameters: Parámetros base de la estrategia
            optimization_parameters: Parámetros a optimizar
            method: Método de optimización ('genetic_algorithm', 'grid_search', 'bayesian')
        
        Returns:
            Resumen de la optimización
        """
        start_time = datetime.now()
        trading_logger.logger.info(f"🔧 Iniciando optimización de {strategy_class.__name__} con {method}")
        
        try:
            # Obtener datos históricos
            historical_data = await self._get_optimization_data()
            if historical_data.empty:
                raise ValueError("No hay datos suficientes para optimización")
            
            # Dividir datos
            train_data, validation_data = self._split_data(historical_data)
            
            # Ejecutar optimización según el método
            if method == "genetic_algorithm":
                best_result, total_iterations, convergence_gen = await self._genetic_algorithm_optimization(
                    strategy_class, base_parameters, optimization_parameters, train_data
                )
            elif method == "grid_search":
                best_result, total_iterations, convergence_gen = await self._grid_search_optimization(
                    strategy_class, base_parameters, optimization_parameters, train_data
                )
            elif method == "bayesian":
                best_result, total_iterations, convergence_gen = await self._bayesian_optimization(
                    strategy_class, base_parameters, optimization_parameters, train_data
                )
            else:
                raise ValueError(f"Método de optimización no soportado: {method}")
            
            # Validar mejor resultado
            validation_score = await self._validate_result(
                strategy_class, best_result.parameters, validation_data
            )
            best_result.validation_score = validation_score
            
            # Calcular mejora
            baseline_score = await self._get_baseline_score(
                strategy_class, base_parameters, train_data
            )
            improvement = ((best_result.fitness_score - baseline_score) / baseline_score * 100) if baseline_score > 0 else 0
            
            # Generar recomendaciones
            recommendations = self._generate_optimization_recommendations(
                best_result, baseline_score, improvement
            )
            
            # Crear resumen
            end_time = datetime.now()
            summary = OptimizationSummary(
                strategy_name=strategy_class.__name__,
                optimization_method=method,
                start_time=start_time,
                end_time=end_time,
                total_iterations=total_iterations,
                best_result=best_result,
                improvement_percentage=improvement,
                convergence_generation=convergence_gen,
                final_recommendations=recommendations
            )
            
            # Guardar en historial
            self.optimization_history.append(summary)
            self.current_optimization = summary
            
            trading_logger.logger.info(f"✅ Optimización completada en {end_time - start_time}")
            trading_logger.logger.info(f"📈 Mejora obtenida: {improvement:.2f}%")
            
            return summary
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error en optimización: {e}")
            raise
    
    async def _genetic_algorithm_optimization(
        self,
        strategy_class: type,
        base_parameters: Dict[str, Any],
        optimization_parameters: List[OptimizationParameter],
        data: pd.DataFrame
    ) -> Tuple[OptimizationResult, int, int]:
        """Optimización usando algoritmo genético."""
        config = self.optimization_config['genetic_algorithm']
        
        # Inicializar población
        population = self._initialize_population(
            optimization_parameters, config['population_size']
        )
        
        best_result = None
        convergence_generation = 0
        total_iterations = 0
        
        for generation in range(config['generations']):
            trading_logger.logger.info(f"🧬 Generación {generation + 1}/{config['generations']}")
            
            # Evaluar población
            fitness_scores = []
            for individual in population:
                parameters = {**base_parameters, **individual}
                fitness = await self._evaluate_parameters(strategy_class, parameters, data)
                fitness_scores.append(fitness)
                total_iterations += 1
            
            # Encontrar mejor individuo de esta generación
            best_idx = np.argmax(fitness_scores)
            current_best = OptimizationResult(
                parameters={**base_parameters, **population[best_idx]},
                fitness_score=fitness_scores[best_idx],
                backtest_results={},  # Se llenará después
                validation_score=0.0,
                generation=generation
            )
            
            if best_result is None or current_best.fitness_score > best_result.fitness_score:
                best_result = current_best
                convergence_generation = generation
            
            # Selección, cruce y mutación
            population = self._genetic_operations(
                population, fitness_scores, config
            )
            
            # Criterio de parada temprana
            if generation - convergence_generation > 10:  # Sin mejora en 10 generaciones
                trading_logger.logger.info(f"🛑 Convergencia temprana en generación {generation}")
                break
        
        # Obtener resultados detallados del mejor
        best_result.backtest_results = await self._get_detailed_backtest(
            strategy_class, best_result.parameters, data
        )
        
        return best_result, total_iterations, convergence_generation
    
    async def _grid_search_optimization(
        self,
        strategy_class: type,
        base_parameters: Dict[str, Any],
        optimization_parameters: List[OptimizationParameter],
        data: pd.DataFrame
    ) -> Tuple[OptimizationResult, int, int]:
        """Optimización usando grid search."""
        # Generar todas las combinaciones
        param_ranges = []
        param_names = []
        
        for param in optimization_parameters:
            if param.parameter_type == "int":
                values = list(range(int(param.min_value), int(param.max_value) + 1, int(param.step)))
            else:
                values = np.arange(param.min_value, param.max_value + param.step, param.step).tolist()
            
            param_ranges.append(values)
            param_names.append(param.name)
        
        # Limitar combinaciones si son demasiadas
        all_combinations = list(product(*param_ranges))
        max_combinations = self.optimization_config['grid_search']['max_combinations']
        
        if len(all_combinations) > max_combinations:
            # Muestreo aleatorio
            combinations = random.sample(all_combinations, max_combinations)
            trading_logger.logger.info(f"🎲 Muestreando {max_combinations} de {len(all_combinations)} combinaciones")
        else:
            combinations = all_combinations
        
        best_result = None
        total_iterations = len(combinations)
        
        for i, combination in enumerate(combinations):
            if i % 10 == 0:
                trading_logger.logger.info(f"🔍 Evaluando combinación {i + 1}/{len(combinations)}")
            
            # Crear parámetros
            parameters = dict(zip(param_names, combination))
            full_parameters = {**base_parameters, **parameters}
            
            # Evaluar
            fitness = await self._evaluate_parameters(strategy_class, full_parameters, data)
            
            result = OptimizationResult(
                parameters=full_parameters,
                fitness_score=fitness,
                backtest_results={},
                validation_score=0.0,
                generation=0
            )
            
            if best_result is None or result.fitness_score > best_result.fitness_score:
                best_result = result
        
        # Obtener resultados detallados
        best_result.backtest_results = await self._get_detailed_backtest(
            strategy_class, best_result.parameters, data
        )
        
        return best_result, total_iterations, 0
    
    async def _bayesian_optimization(
        self,
        strategy_class: type,
        base_parameters: Dict[str, Any],
        optimization_parameters: List[OptimizationParameter],
        data: pd.DataFrame
    ) -> Tuple[OptimizationResult, int, int]:
        """Optimización bayesiana (implementación simplificada)."""
        # Implementación simplificada usando muestreo inteligente
        config = self.optimization_config['bayesian']
        
        # Puntos iniciales aleatorios
        initial_points = []
        for _ in range(config['n_initial_points']):
            point = {}
            for param in optimization_parameters:
                if param.parameter_type == "int":
                    value = random.randint(int(param.min_value), int(param.max_value))
                else:
                    value = random.uniform(param.min_value, param.max_value)
                point[param.name] = value
            initial_points.append(point)
        
        best_result = None
        all_results = []
        
        # Evaluar puntos iniciales
        for i, point in enumerate(initial_points):
            trading_logger.logger.info(f"🎯 Evaluando punto inicial {i + 1}/{len(initial_points)}")
            
            parameters = {**base_parameters, **point}
            fitness = await self._evaluate_parameters(strategy_class, parameters, data)
            
            result = OptimizationResult(
                parameters=parameters,
                fitness_score=fitness,
                backtest_results={},
                validation_score=0.0,
                generation=0
            )
            
            all_results.append(result)
            
            if best_result is None or result.fitness_score > best_result.fitness_score:
                best_result = result
        
        # Puntos adicionales usando exploración inteligente
        remaining_calls = config['n_calls'] - config['n_initial_points']
        
        for i in range(remaining_calls):
            # Estrategia simple: explorar alrededor del mejor punto actual
            exploration_point = self._generate_exploration_point(
                best_result.parameters, optimization_parameters
            )
            
            parameters = {**base_parameters, **exploration_point}
            fitness = await self._evaluate_parameters(strategy_class, parameters, data)
            
            result = OptimizationResult(
                parameters=parameters,
                fitness_score=fitness,
                backtest_results={},
                validation_score=0.0,
                generation=i + config['n_initial_points']
            )
            
            all_results.append(result)
            
            if result.fitness_score > best_result.fitness_score:
                best_result = result
        
        # Obtener resultados detallados
        best_result.backtest_results = await self._get_detailed_backtest(
            strategy_class, best_result.parameters, data
        )
        
        return best_result, config['n_calls'], 0
    
    def _initialize_population(
        self, 
        optimization_parameters: List[OptimizationParameter], 
        population_size: int
    ) -> List[Dict[str, Any]]:
        """Inicializar población para algoritmo genético."""
        population = []
        
        for _ in range(population_size):
            individual = {}
            for param in optimization_parameters:
                if param.parameter_type == "int":
                    value = random.randint(int(param.min_value), int(param.max_value))
                elif param.parameter_type == "bool":
                    value = random.choice([True, False])
                else:
                    value = random.uniform(param.min_value, param.max_value)
                
                individual[param.name] = value
            
            population.append(individual)
        
        return population
    
    def _genetic_operations(
        self, 
        population: List[Dict[str, Any]], 
        fitness_scores: List[float],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Operaciones genéticas: selección, cruce y mutación."""
        # Selección por torneo
        new_population = []
        
        # Mantener élite
        elite_indices = np.argsort(fitness_scores)[-config['elite_size']:]
        for idx in elite_indices:
            new_population.append(population[idx].copy())
        
        # Generar resto de la población
        while len(new_population) < len(population):
            # Selección de padres
            parent1 = self._tournament_selection(population, fitness_scores)
            parent2 = self._tournament_selection(population, fitness_scores)
            
            # Cruce
            if random.random() < config['crossover_rate']:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()
            
            # Mutación
            if random.random() < config['mutation_rate']:
                child1 = self._mutate(child1)
            if random.random() < config['mutation_rate']:
                child2 = self._mutate(child2)
            
            new_population.extend([child1, child2])
        
        return new_population[:len(population)]
    
    def _tournament_selection(
        self, 
        population: List[Dict[str, Any]], 
        fitness_scores: List[float],
        tournament_size: int = 3
    ) -> Dict[str, Any]:
        """Selección por torneo."""
        tournament_indices = random.sample(range(len(population)), tournament_size)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_idx = tournament_indices[np.argmax(tournament_fitness)]
        return population[winner_idx].copy()
    
    def _crossover(
        self, 
        parent1: Dict[str, Any], 
        parent2: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Cruce uniforme."""
        child1, child2 = parent1.copy(), parent2.copy()
        
        for key in parent1.keys():
            if random.random() < 0.5:
                child1[key], child2[key] = child2[key], child1[key]
        
        return child1, child2
    
    def _mutate(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """Mutación gaussiana."""
        mutated = individual.copy()
        
        for key, value in mutated.items():
            if isinstance(value, (int, float)):
                # Mutación gaussiana (5% del valor)
                noise = np.random.normal(0, abs(value) * 0.05)
                mutated[key] = value + noise
                
                # Asegurar que esté en rango válido (simplificado)
                if isinstance(value, int):
                    mutated[key] = int(max(1, mutated[key]))
                else:
                    mutated[key] = max(0.01, mutated[key])
        
        return mutated
    
    def _generate_exploration_point(
        self,
        best_parameters: Dict[str, Any],
        optimization_parameters: List[OptimizationParameter]
    ) -> Dict[str, Any]:
        """Generar punto de exploración alrededor del mejor."""
        exploration_point = {}
        
        for param in optimization_parameters:
            if param.name in best_parameters:
                current_value = best_parameters[param.name]
                
                # Explorar alrededor del valor actual
                range_size = (param.max_value - param.min_value) * 0.1  # 10% del rango
                
                if param.parameter_type == "int":
                    new_value = int(current_value + random.uniform(-range_size, range_size))
                    new_value = max(int(param.min_value), min(int(param.max_value), new_value))
                else:
                    new_value = current_value + random.uniform(-range_size, range_size)
                    new_value = max(param.min_value, min(param.max_value, new_value))
                
                exploration_point[param.name] = new_value
        
        return exploration_point
    
    async def _get_optimization_data(self) -> pd.DataFrame:
        """Obtener datos para optimización."""
        symbol = self.settings.DEFAULT_SYMBOL
        
        # 4 meses de datos para optimización
        end_date = datetime.now()
        start_date = end_date - timedelta(days=120)
        
        return await self.market_data.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe='1h'
        )
    
    def _split_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Dividir datos en entrenamiento y validación."""
        split_point = int(len(data) * 0.7)  # 70% entrenamiento, 30% validación
        
        train_data = data.iloc[:split_point].copy()
        validation_data = data.iloc[split_point:].copy()
        
        return train_data, validation_data
    
    async def _evaluate_parameters(
        self,
        strategy_class: type,
        parameters: Dict[str, Any],
        data: pd.DataFrame
    ) -> float:
        """Evaluar parámetros de estrategia."""
        try:
            # Crear estrategia con parámetros
            strategy = strategy_class(**parameters)
            
            # Ejecutar backtesting
            results = self.backtest_engine.run_backtest(strategy, data, self.settings.DEFAULT_SYMBOL)
            
            # Calcular fitness score
            return self._calculate_fitness_score(results)
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error evaluando parámetros: {e}")
            return 0.0
    
    def _calculate_fitness_score(self, results: Dict[str, Any]) -> float:
        """Calcular score de fitness."""
        if results['total_trades'] == 0:
            return 0.0
        
        # Componentes del fitness
        return_component = min(results['total_return'] / 100, 2.0)  # Máximo 200%
        win_rate_component = results['win_rate'] / 100
        sharpe_component = min(max(results['sharpe_ratio'] / 3, 0), 1.0)
        drawdown_penalty = max(0, 1 - results['max_drawdown'] / 30)
        
        # Fitness ponderado
        fitness = (
            return_component * 0.4 +
            win_rate_component * 0.2 +
            sharpe_component * 0.3 +
            drawdown_penalty * 0.1
        )
        
        return max(0, fitness)
    
    async def _validate_result(
        self,
        strategy_class: type,
        parameters: Dict[str, Any],
        validation_data: pd.DataFrame
    ) -> float:
        """Validar resultado en datos separados."""
        return await self._evaluate_parameters(strategy_class, parameters, validation_data)
    
    async def _get_baseline_score(
        self,
        strategy_class: type,
        base_parameters: Dict[str, Any],
        data: pd.DataFrame
    ) -> float:
        """Obtener score baseline."""
        return await self._evaluate_parameters(strategy_class, base_parameters, data)
    
    async def _get_detailed_backtest(
        self,
        strategy_class: type,
        parameters: Dict[str, Any],
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Obtener backtest detallado."""
        strategy = strategy_class(**parameters)
        return self.backtest_engine.run_backtest(strategy, data, self.settings.DEFAULT_SYMBOL)
    
    def _generate_optimization_recommendations(
        self,
        best_result: OptimizationResult,
        baseline_score: float,
        improvement: float
    ) -> List[str]:
        """Generar recomendaciones de optimización."""
        recommendations = []
        
        if improvement > 20:
            recommendations.append(f"🚀 Excelente mejora del {improvement:.1f}%")
        elif improvement > 10:
            recommendations.append(f"📈 Buena mejora del {improvement:.1f}%")
        elif improvement > 0:
            recommendations.append(f"✅ Mejora modesta del {improvement:.1f}%")
        else:
            recommendations.append("⚠️ No se logró mejora significativa")
        
        # Análisis de parámetros
        recommendations.append("🔧 Parámetros optimizados:")
        for param, value in best_result.parameters.items():
            if isinstance(value, float):
                recommendations.append(f"  • {param}: {value:.3f}")
            else:
                recommendations.append(f"  • {param}: {value}")
        
        # Recomendaciones de uso
        if best_result.validation_score > 0.7:
            recommendations.append("✅ Estrategia lista para paper trading")
        elif best_result.validation_score > 0.5:
            recommendations.append("⚠️ Probar más en simulación antes de usar")
        else:
            recommendations.append("🚨 Requiere más optimización")
        
        return recommendations
    
    async def get_optimization_summary(self) -> Dict[str, Any]:
        """Obtener resumen de optimizaciones."""
        if not self.optimization_history:
            return {"message": "No hay historial de optimización disponible"}
        
        latest = self.optimization_history[-1]
        
        return {
            "agent_id": self.agent_id,
            "total_optimizations": len(self.optimization_history),
            "latest_optimization": {
                "strategy": latest.strategy_name,
                "method": latest.optimization_method,
                "improvement": latest.improvement_percentage,
                "duration": str(latest.end_time - latest.start_time),
                "iterations": latest.total_iterations,
                "best_fitness": latest.best_result.fitness_score,
                "recommendations": latest.final_recommendations
            },
            "average_improvement": np.mean([opt.improvement_percentage for opt in self.optimization_history])
        }
    
    async def stop(self):
        """Detener el agente de optimización."""
        trading_logger.logger.info(f"🛑 Deteniendo Optimizer Agent {self.agent_id}")
        self.is_running = False
        
        trading_logger.agent_action(
            agent_name=self.agent_id,
            action="stop",
            result="success"
        )