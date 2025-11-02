"""
Optimizer Agent - Agente especializado en optimización de estrategias y parámetros
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import optuna
import json

from backend.agents.base_agent import BaseAgent, AgentTask
from backend.services.binance_service import BinanceService
from backend.services.backtesting_service import BacktestingService
from backend.core.database import DatabaseManager
from backend.core.config import settings

class OptimizerAgent(BaseAgent):
    """
    Agente especializado en optimización de estrategias y parámetros
    
    Responsabilidades:
    - Optimizar parámetros de estrategias de trading
    - Realizar backtesting automatizado
    - Encontrar configuraciones óptimas usando algoritmos genéticos/bayesianos
    - Evaluar performance de diferentes configuraciones
    - Sugerir mejoras en estrategias existentes
    """
    
    def __init__(self):
        super().__init__(
            name="OptimizerAgent",
            description="Agente especializado en optimización de estrategias y parámetros"
        )
        self.binance_service: Optional[BinanceService] = None
        self.backtesting_service: Optional[BacktestingService] = None
        self.optimization_history = {}
        self.current_optimizations = {}
        
    async def _initialize_agent(self):
        """Inicializar servicios del agente optimizador"""
        self.binance_service = BinanceService()
        await self.binance_service.initialize()
        
        self.backtesting_service = BacktestingService()
        await self.backtesting_service.initialize()
        
        self.logger.info("OptimizerAgent inicializado con servicios de backtesting y optimización")
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        Calcular el Sharpe ratio de una serie de retornos
        
        Args:
            returns: Serie de retornos
            risk_free_rate: Tasa libre de riesgo anual (default: 2%)
            
        Returns:
            Sharpe ratio
        """
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
            
        # Convertir tasa libre de riesgo a diaria
        daily_risk_free_rate = risk_free_rate / 252
        
        # Calcular exceso de retorno
        excess_returns = returns - daily_risk_free_rate
        
        # Calcular Sharpe ratio
        sharpe = excess_returns.mean() / returns.std()
        
        # Anualizar
        return sharpe * np.sqrt(252)
    
    async def _process_task(self, task: AgentTask) -> Any:
        """Procesar tareas de optimización"""
        task_type = task.task_type
        parameters = task.parameters
        
        if task_type == "optimize_strategy":
            return await self._optimize_strategy(parameters)
        elif task_type == "parameter_sweep":
            return await self._parameter_sweep(parameters)
        elif task_type == "genetic_optimization":
            return await self._genetic_optimization(parameters)
        elif task_type == "bayesian_optimization":
            return await self._bayesian_optimization(parameters)
        elif task_type == "walk_forward_analysis":
            return await self._walk_forward_analysis(parameters)
        elif task_type == "strategy_comparison":
            return await self._strategy_comparison(parameters)
        elif task_type == "performance_analysis":
            return await self._performance_analysis(parameters)
        else:
            raise ValueError(f"Tipo de tarea no soportado: {task_type}")
    
    async def _optimize_strategy(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimizar una estrategia de trading
        
        Args:
            parameters: Configuración de optimización
            
        Returns:
            Resultados de optimización
        """
        strategy_name = parameters.get("strategy_name")
        symbol = parameters.get("symbol", settings.DEFAULT_TRADING_PAIR)
        optimization_method = parameters.get("method", "bayesian")
        parameter_ranges = parameters.get("parameter_ranges", {})
        objective = parameters.get("objective", "sharpe_ratio")
        
        if not strategy_name:
            raise ValueError("Se requiere especificar strategy_name")
        
        self.logger.info(f"Optimizando estrategia {strategy_name} para {symbol}")
        
        try:
            optimization_id = f"opt_{strategy_name}_{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Registrar optimización en progreso
            self.current_optimizations[optimization_id] = {
                "strategy_name": strategy_name,
                "symbol": symbol,
                "method": optimization_method,
                "status": "running",
                "start_time": datetime.utcnow(),
                "progress": 0
            }
            
            # Ejecutar optimización según método
            if optimization_method == "bayesian":
                results = await self._bayesian_optimization({
                    "strategy_name": strategy_name,
                    "symbol": symbol,
                    "parameter_ranges": parameter_ranges,
                    "objective": objective,
                    "n_trials": parameters.get("n_trials", 100)
                })
            elif optimization_method == "genetic":
                results = await self._genetic_optimization({
                    "strategy_name": strategy_name,
                    "symbol": symbol,
                    "parameter_ranges": parameter_ranges,
                    "objective": objective,
                    "population_size": parameters.get("population_size", 50),
                    "generations": parameters.get("generations", 20)
                })
            elif optimization_method == "grid_search":
                results = await self._parameter_sweep({
                    "strategy_name": strategy_name,
                    "symbol": symbol,
                    "parameter_ranges": parameter_ranges,
                    "objective": objective
                })
            else:
                raise ValueError(f"Método de optimización no soportado: {optimization_method}")
            
            # Actualizar estado
            self.current_optimizations[optimization_id]["status"] = "completed"
            self.current_optimizations[optimization_id]["end_time"] = datetime.utcnow()
            self.current_optimizations[optimization_id]["results"] = results
            
            # Guardar en historial
            self.optimization_history[optimization_id] = self.current_optimizations[optimization_id]
            
            # Guardar resultados en base de datos
            await self._save_optimization_results(optimization_id, results)
            
            return {
                "optimization_id": optimization_id,
                "strategy_name": strategy_name,
                "symbol": symbol,
                "method": optimization_method,
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizando estrategia: {e}")
            if optimization_id in self.current_optimizations:
                self.current_optimizations[optimization_id]["status"] = "error"
                self.current_optimizations[optimization_id]["error"] = str(e)
            raise
    
    async def _bayesian_optimization(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimización bayesiana usando Optuna"""
        strategy_name = parameters.get("strategy_name")
        symbol = parameters.get("symbol")
        parameter_ranges = parameters.get("parameter_ranges", {})
        objective = parameters.get("objective", "sharpe_ratio")
        n_trials = parameters.get("n_trials", 100)
        
        self.logger.info(f"Iniciando optimización bayesiana con {n_trials} trials")
        
        try:
            # Crear estudio de Optuna
            study = optuna.create_study(
                direction="maximize" if objective in ["sharpe_ratio", "total_return", "win_rate"] else "minimize",
                study_name=f"{strategy_name}_{symbol}_optimization"
            )
            
            # Función objetivo
            async def objective_function(trial):
                # Generar parámetros para este trial
                trial_params = {}
                for param_name, param_range in parameter_ranges.items():
                    if isinstance(param_range, dict):
                        if param_range.get("type") == "int":
                            trial_params[param_name] = trial.suggest_int(
                                param_name, 
                                param_range["min"], 
                                param_range["max"]
                            )
                        elif param_range.get("type") == "float":
                            trial_params[param_name] = trial.suggest_float(
                                param_name, 
                                param_range["min"], 
                                param_range["max"]
                            )
                        elif param_range.get("type") == "categorical":
                            trial_params[param_name] = trial.suggest_categorical(
                                param_name, 
                                param_range["choices"]
                            )
                    else:
                        # Asumir rango numérico simple
                        trial_params[param_name] = trial.suggest_float(
                            param_name, 
                            param_range[0], 
                            param_range[1]
                        )
                
                # Ejecutar backtest con estos parámetros
                backtest_result = await self.backtesting_service.run_backtest({
                    "strategy_name": strategy_name,
                    "symbol": symbol,
                    "parameters": trial_params,
                    "start_date": parameters.get("start_date", "2023-01-01"),
                    "end_date": parameters.get("end_date", "2024-01-01")
                })
                
                if not backtest_result.get("success", False):
                    return float('-inf')  # Penalizar fallos
                
                # Extraer métrica objetivo
                metrics = backtest_result.get("metrics", {})
                if objective == "sharpe_ratio":
                    return metrics.get("sharpe_ratio", 0)
                elif objective == "total_return":
                    return metrics.get("total_return", 0)
                elif objective == "win_rate":
                    return metrics.get("win_rate", 0)
                elif objective == "max_drawdown":
                    return -metrics.get("max_drawdown", 1)  # Minimizar drawdown
                else:
                    return metrics.get(objective, 0)
            
            # Ejecutar optimización
            best_params = None
            best_value = float('-inf')
            trial_results = []
            
            for i in range(n_trials):
                trial = study.ask()
                
                try:
                    value = await objective_function(trial)
                    study.tell(trial, value)
                    
                    trial_results.append({
                        "trial_number": i + 1,
                        "parameters": trial.params,
                        "value": value
                    })
                    
                    if value > best_value:
                        best_value = value
                        best_params = trial.params.copy()
                    
                    # Actualizar progreso
                    progress = ((i + 1) / n_trials) * 100
                    self.logger.debug(f"Trial {i+1}/{n_trials} completado. Mejor valor: {best_value:.4f}")
                    
                except Exception as e:
                    self.logger.warning(f"Error en trial {i+1}: {e}")
                    study.tell(trial, float('-inf'))
            
            # Ejecutar backtest final con mejores parámetros
            final_backtest = await self.backtesting_service.run_backtest({
                "strategy_name": strategy_name,
                "symbol": symbol,
                "parameters": best_params,
                "start_date": parameters.get("start_date", "2023-01-01"),
                "end_date": parameters.get("end_date", "2024-01-01")
            })
            
            return {
                "method": "bayesian_optimization",
                "best_parameters": best_params,
                "best_value": best_value,
                "objective": objective,
                "n_trials": n_trials,
                "final_backtest": final_backtest,
                "trial_history": trial_results[-10:],  # Últimos 10 trials
                "optimization_summary": {
                    "total_trials": n_trials,
                    "successful_trials": len([r for r in trial_results if r["value"] > float('-inf')]),
                    "improvement_over_trials": best_value
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error en optimización bayesiana: {e}")
            raise
    
    async def _genetic_optimization(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimización usando algoritmo genético simplificado"""
        strategy_name = parameters.get("strategy_name")
        symbol = parameters.get("symbol")
        parameter_ranges = parameters.get("parameter_ranges", {})
        objective = parameters.get("objective", "sharpe_ratio")
        population_size = parameters.get("population_size", 50)
        generations = parameters.get("generations", 20)
        
        self.logger.info(f"Iniciando optimización genética: {population_size} individuos, {generations} generaciones")
        
        try:
            # Generar población inicial
            population = []
            for _ in range(population_size):
                individual = {}
                for param_name, param_range in parameter_ranges.items():
                    if isinstance(param_range, dict):
                        if param_range.get("type") == "int":
                            individual[param_name] = np.random.randint(param_range["min"], param_range["max"] + 1)
                        elif param_range.get("type") == "float":
                            individual[param_name] = np.random.uniform(param_range["min"], param_range["max"])
                        elif param_range.get("type") == "categorical":
                            individual[param_name] = np.random.choice(param_range["choices"])
                    else:
                        individual[param_name] = np.random.uniform(param_range[0], param_range[1])
                population.append(individual)
            
            best_individual = None
            best_fitness = float('-inf')
            generation_history = []
            
            for generation in range(generations):
                # Evaluar fitness de la población
                fitness_scores = []
                
                for individual in population:
                    backtest_result = await self.backtesting_service.run_backtest({
                        "strategy_name": strategy_name,
                        "symbol": symbol,
                        "parameters": individual,
                        "start_date": parameters.get("start_date", "2023-01-01"),
                        "end_date": parameters.get("end_date", "2024-01-01")
                    })
                    
                    if backtest_result.get("success", False):
                        metrics = backtest_result.get("metrics", {})
                        fitness = metrics.get(objective, 0)
                    else:
                        fitness = float('-inf')
                    
                    fitness_scores.append(fitness)
                    
                    if fitness > best_fitness:
                        best_fitness = fitness
                        best_individual = individual.copy()
                
                # Registrar estadísticas de la generación
                generation_stats = {
                    "generation": generation + 1,
                    "best_fitness": max(fitness_scores),
                    "average_fitness": np.mean([f for f in fitness_scores if f > float('-inf')]),
                    "worst_fitness": min([f for f in fitness_scores if f > float('-inf')])
                }
                generation_history.append(generation_stats)
                
                self.logger.debug(f"Generación {generation+1}: Mejor fitness = {generation_stats['best_fitness']:.4f}")
                
                # Selección y reproducción (implementación simplificada)
                if generation < generations - 1:
                    # Seleccionar mejores individuos (elitismo)
                    elite_size = population_size // 4
                    sorted_indices = np.argsort(fitness_scores)[::-1]
                    elite = [population[i] for i in sorted_indices[:elite_size]]
                    
                    # Generar nueva población
                    new_population = elite.copy()
                    
                    while len(new_population) < population_size:
                        # Selección por torneo
                        parent1 = self._tournament_selection(population, fitness_scores)
                        parent2 = self._tournament_selection(population, fitness_scores)
                        
                        # Cruzamiento
                        child = self._crossover(parent1, parent2, parameter_ranges)
                        
                        # Mutación
                        child = self._mutate(child, parameter_ranges, mutation_rate=0.1)
                        
                        new_population.append(child)
                    
                    population = new_population
            
            # Ejecutar backtest final
            final_backtest = await self.backtesting_service.run_backtest({
                "strategy_name": strategy_name,
                "symbol": symbol,
                "parameters": best_individual,
                "start_date": parameters.get("start_date", "2023-01-01"),
                "end_date": parameters.get("end_date", "2024-01-01")
            })
            
            return {
                "method": "genetic_optimization",
                "best_parameters": best_individual,
                "best_fitness": best_fitness,
                "objective": objective,
                "population_size": population_size,
                "generations": generations,
                "final_backtest": final_backtest,
                "generation_history": generation_history,
                "optimization_summary": {
                    "total_evaluations": population_size * generations,
                    "final_improvement": best_fitness,
                    "convergence_generation": next((i for i, g in enumerate(generation_history) if g["best_fitness"] == best_fitness), generations)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error en optimización genética: {e}")
            raise
    
    def _tournament_selection(self, population: List[Dict], fitness_scores: List[float], tournament_size: int = 3) -> Dict:
        """Selección por torneo"""
        tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_index = tournament_indices[np.argmax(tournament_fitness)]
        return population[winner_index]
    
    def _crossover(self, parent1: Dict, parent2: Dict, parameter_ranges: Dict) -> Dict:
        """Cruzamiento de dos individuos"""
        child = {}
        for param_name in parent1.keys():
            if np.random.random() < 0.5:
                child[param_name] = parent1[param_name]
            else:
                child[param_name] = parent2[param_name]
        return child
    
    def _mutate(self, individual: Dict, parameter_ranges: Dict, mutation_rate: float = 0.1) -> Dict:
        """Mutación de un individuo"""
        mutated = individual.copy()
        
        for param_name, param_range in parameter_ranges.items():
            if np.random.random() < mutation_rate:
                if isinstance(param_range, dict):
                    if param_range.get("type") == "int":
                        mutated[param_name] = np.random.randint(param_range["min"], param_range["max"] + 1)
                    elif param_range.get("type") == "float":
                        mutated[param_name] = np.random.uniform(param_range["min"], param_range["max"])
                    elif param_range.get("type") == "categorical":
                        mutated[param_name] = np.random.choice(param_range["choices"])
                else:
                    mutated[param_name] = np.random.uniform(param_range[0], param_range[1])
        
        return mutated
    
    async def _parameter_sweep(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Búsqueda exhaustiva de parámetros (grid search)"""
        strategy_name = parameters.get("strategy_name")
        symbol = parameters.get("symbol")
        parameter_ranges = parameters.get("parameter_ranges", {})
        objective = parameters.get("objective", "sharpe_ratio")
        
        self.logger.info(f"Iniciando búsqueda exhaustiva de parámetros")
        
        try:
            # Generar todas las combinaciones de parámetros
            param_combinations = self._generate_parameter_combinations(parameter_ranges)
            
            if len(param_combinations) > 1000:
                self.logger.warning(f"Muchas combinaciones ({len(param_combinations)}). Limitando a 1000.")
                param_combinations = param_combinations[:1000]
            
            results = []
            best_params = None
            best_value = float('-inf')
            
            for i, params in enumerate(param_combinations):
                try:
                    backtest_result = await self.backtesting_service.run_backtest({
                        "strategy_name": strategy_name,
                        "symbol": symbol,
                        "parameters": params,
                        "start_date": parameters.get("start_date", "2023-01-01"),
                        "end_date": parameters.get("end_date", "2024-01-01")
                    })
                    
                    if backtest_result.get("success", False):
                        metrics = backtest_result.get("metrics", {})
                        value = metrics.get(objective, 0)
                        
                        results.append({
                            "parameters": params,
                            "value": value,
                            "metrics": metrics
                        })
                        
                        if value > best_value:
                            best_value = value
                            best_params = params.copy()
                    
                    if (i + 1) % 50 == 0:
                        self.logger.debug(f"Procesadas {i+1}/{len(param_combinations)} combinaciones")
                        
                except Exception as e:
                    self.logger.warning(f"Error en combinación {i+1}: {e}")
            
            # Ejecutar backtest final
            final_backtest = await self.backtesting_service.run_backtest({
                "strategy_name": strategy_name,
                "symbol": symbol,
                "parameters": best_params,
                "start_date": parameters.get("start_date", "2023-01-01"),
                "end_date": parameters.get("end_date", "2024-01-01")
            })
            
            return {
                "method": "parameter_sweep",
                "best_parameters": best_params,
                "best_value": best_value,
                "objective": objective,
                "total_combinations": len(param_combinations),
                "successful_combinations": len(results),
                "final_backtest": final_backtest,
                "top_results": sorted(results, key=lambda x: x["value"], reverse=True)[:10]
            }
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda de parámetros: {e}")
            raise
    
    def _generate_parameter_combinations(self, parameter_ranges: Dict) -> List[Dict]:
        """Generar todas las combinaciones de parámetros"""
        import itertools
        
        param_names = list(parameter_ranges.keys())
        param_values = []
        
        for param_name, param_range in parameter_ranges.items():
            if isinstance(param_range, dict):
                if param_range.get("type") == "int":
                    values = list(range(param_range["min"], param_range["max"] + 1, param_range.get("step", 1)))
                elif param_range.get("type") == "float":
                    step = param_range.get("step", (param_range["max"] - param_range["min"]) / 10)
                    values = list(np.arange(param_range["min"], param_range["max"] + step, step))
                elif param_range.get("type") == "categorical":
                    values = param_range["choices"]
                else:
                    values = [param_range.get("default", 1)]
            else:
                # Asumir rango numérico simple
                values = list(np.linspace(param_range[0], param_range[1], 10))
            
            param_values.append(values)
        
        # Generar todas las combinaciones
        combinations = []
        for combination in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combination))
            combinations.append(param_dict)
        
        return combinations
    
    async def _walk_forward_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis walk-forward para validar robustez"""
        strategy_name = parameters.get("strategy_name")
        symbol = parameters.get("symbol")
        base_parameters = parameters.get("parameters", {})
        window_size = parameters.get("window_size", 90)  # días
        step_size = parameters.get("step_size", 30)  # días
        
        self.logger.info(f"Iniciando análisis walk-forward con ventana de {window_size} días")
        
        try:
            # Obtener rango de fechas total
            start_date = datetime.strptime(parameters.get("start_date", "2023-01-01"), "%Y-%m-%d")
            end_date = datetime.strptime(parameters.get("end_date", "2024-01-01"), "%Y-%m-%d")
            
            results = []
            current_date = start_date
            
            while current_date + timedelta(days=window_size) <= end_date:
                window_start = current_date
                window_end = current_date + timedelta(days=window_size)
                
                # Ejecutar backtest en esta ventana
                backtest_result = await self.backtesting_service.run_backtest({
                    "strategy_name": strategy_name,
                    "symbol": symbol,
                    "parameters": base_parameters,
                    "start_date": window_start.strftime("%Y-%m-%d"),
                    "end_date": window_end.strftime("%Y-%m-%d")
                })
                
                if backtest_result.get("success", False):
                    metrics = backtest_result.get("metrics", {})
                    results.append({
                        "window_start": window_start.strftime("%Y-%m-%d"),
                        "window_end": window_end.strftime("%Y-%m-%d"),
                        "metrics": metrics
                    })
                
                current_date += timedelta(days=step_size)
            
            # Calcular estadísticas agregadas
            if results:
                all_returns = [r["metrics"].get("total_return", 0) for r in results]
                all_sharpe = [r["metrics"].get("sharpe_ratio", 0) for r in results if r["metrics"].get("sharpe_ratio", 0) != 0]
                all_drawdowns = [r["metrics"].get("max_drawdown", 0) for r in results]
                
                aggregate_stats = {
                    "total_windows": len(results),
                    "average_return": np.mean(all_returns),
                    "return_std": np.std(all_returns),
                    "average_sharpe": np.mean(all_sharpe) if all_sharpe else 0,
                    "sharpe_std": np.std(all_sharpe) if all_sharpe else 0,
                    "average_drawdown": np.mean(all_drawdowns),
                    "max_drawdown": max(all_drawdowns) if all_drawdowns else 0,
                    "positive_windows": len([r for r in all_returns if r > 0]),
                    "win_rate": len([r for r in all_returns if r > 0]) / len(all_returns) if all_returns else 0
                }
            else:
                aggregate_stats = {}
            
            return {
                "method": "walk_forward_analysis",
                "strategy_name": strategy_name,
                "symbol": symbol,
                "parameters": base_parameters,
                "window_size": window_size,
                "step_size": step_size,
                "window_results": results,
                "aggregate_statistics": aggregate_stats,
                "robustness_score": self._calculate_robustness_score(aggregate_stats)
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis walk-forward: {e}")
            raise
    
    def _calculate_robustness_score(self, stats: Dict[str, Any]) -> float:
        """Calcular score de robustez (0-100)"""
        if not stats:
            return 0
        
        score = 0
        
        # Win rate (30 puntos máximo)
        win_rate = stats.get("win_rate", 0)
        score += min(win_rate * 30, 30)
        
        # Consistencia de Sharpe ratio (25 puntos máximo)
        avg_sharpe = stats.get("average_sharpe", 0)
        sharpe_std = stats.get("sharpe_std", 1)
        if sharpe_std > 0:
            sharpe_consistency = max(0, 1 - (sharpe_std / max(abs(avg_sharpe), 0.1)))
            score += sharpe_consistency * 25
        
        # Drawdown control (25 puntos máximo)
        max_drawdown = stats.get("max_drawdown", 1)
        drawdown_score = max(0, 1 - max_drawdown) * 25
        score += drawdown_score
        
        # Retorno positivo promedio (20 puntos máximo)
        avg_return = stats.get("average_return", 0)
        if avg_return > 0:
            score += min(avg_return * 100, 20)
        
        return min(score, 100)
    
    async def _strategy_comparison(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Comparar múltiples estrategias"""
        strategies = parameters.get("strategies", [])
        symbol = parameters.get("symbol", settings.DEFAULT_TRADING_PAIR)
        
        if len(strategies) < 2:
            raise ValueError("Se necesitan al menos 2 estrategias para comparar")
        
        self.logger.info(f"Comparando {len(strategies)} estrategias")
        
        try:
            comparison_results = []
            
            for strategy_config in strategies:
                strategy_name = strategy_config.get("name")
                strategy_params = strategy_config.get("parameters", {})
                
                backtest_result = await self.backtesting_service.run_backtest({
                    "strategy_name": strategy_name,
                    "symbol": symbol,
                    "parameters": strategy_params,
                    "start_date": parameters.get("start_date", "2023-01-01"),
                    "end_date": parameters.get("end_date", "2024-01-01")
                })
                
                if backtest_result.get("success", False):
                    comparison_results.append({
                        "strategy_name": strategy_name,
                        "parameters": strategy_params,
                        "metrics": backtest_result.get("metrics", {}),
                        "trades": backtest_result.get("total_trades", 0)
                    })
            
            # Ranking por diferentes métricas
            rankings = {}
            metrics_to_rank = ["total_return", "sharpe_ratio", "win_rate", "max_drawdown"]
            
            for metric in metrics_to_rank:
                if metric == "max_drawdown":
                    # Para drawdown, menor es mejor
                    sorted_strategies = sorted(
                        comparison_results, 
                        key=lambda x: x["metrics"].get(metric, 1)
                    )
                else:
                    # Para otras métricas, mayor es mejor
                    sorted_strategies = sorted(
                        comparison_results, 
                        key=lambda x: x["metrics"].get(metric, 0), 
                        reverse=True
                    )
                
                rankings[metric] = [s["strategy_name"] for s in sorted_strategies]
            
            # Calcular score compuesto
            for result in comparison_results:
                score = 0
                for metric in metrics_to_rank:
                    rank = rankings[metric].index(result["strategy_name"]) + 1
                    score += (len(comparison_results) - rank + 1) / len(comparison_results)
                result["composite_score"] = score / len(metrics_to_rank)
            
            # Ordenar por score compuesto
            comparison_results.sort(key=lambda x: x["composite_score"], reverse=True)
            
            return {
                "method": "strategy_comparison",
                "symbol": symbol,
                "strategies_compared": len(strategies),
                "results": comparison_results,
                "rankings": rankings,
                "best_strategy": comparison_results[0]["strategy_name"] if comparison_results else None,
                "summary": {
                    "winner": comparison_results[0] if comparison_results else None,
                    "performance_spread": {
                        "return_range": [
                            min(r["metrics"].get("total_return", 0) for r in comparison_results),
                            max(r["metrics"].get("total_return", 0) for r in comparison_results)
                        ] if comparison_results else [0, 0],
                        "sharpe_range": [
                            min(r["metrics"].get("sharpe_ratio", 0) for r in comparison_results),
                            max(r["metrics"].get("sharpe_ratio", 0) for r in comparison_results)
                        ] if comparison_results else [0, 0]
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error comparando estrategias: {e}")
            raise
    
    async def _performance_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis detallado de performance de una estrategia"""
        strategy_name = parameters.get("strategy_name")
        symbol = parameters.get("symbol")
        strategy_params = parameters.get("parameters", {})
        
        try:
            # Ejecutar backtest detallado
            backtest_result = await self.backtesting_service.run_backtest({
                "strategy_name": strategy_name,
                "symbol": symbol,
                "parameters": strategy_params,
                "start_date": parameters.get("start_date", "2023-01-01"),
                "end_date": parameters.get("end_date", "2024-01-01"),
                "detailed": True
            })
            
            if not backtest_result.get("success", False):
                raise ValueError("Backtest falló")
            
            metrics = backtest_result.get("metrics", {})
            trades = backtest_result.get("trades", [])
            
            # Análisis adicional
            performance_analysis = {
                "basic_metrics": metrics,
                "trade_analysis": self._analyze_trades(trades),
                "risk_metrics": self._calculate_risk_metrics_from_trades(trades),
                "monthly_performance": self._calculate_monthly_performance(trades),
                "drawdown_analysis": self._analyze_drawdowns(trades),
                "performance_attribution": self._analyze_performance_attribution(trades)
            }
            
            return {
                "method": "performance_analysis",
                "strategy_name": strategy_name,
                "symbol": symbol,
                "parameters": strategy_params,
                "analysis": performance_analysis,
                "recommendations": self._generate_performance_recommendations(performance_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis de performance: {e}")
            raise
    
    def _analyze_trades(self, trades: List[Dict]) -> Dict[str, Any]:
        """Analizar trades individuales"""
        if not trades:
            return {"error": "No hay trades para analizar"}
        
        profits = [t.get("pnl", 0) for t in trades]
        winning_trades = [p for p in profits if p > 0]
        losing_trades = [p for p in profits if p < 0]
        
        return {
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(trades) if trades else 0,
            "average_win": np.mean(winning_trades) if winning_trades else 0,
            "average_loss": np.mean(losing_trades) if losing_trades else 0,
            "largest_win": max(winning_trades) if winning_trades else 0,
            "largest_loss": min(losing_trades) if losing_trades else 0,
            "profit_factor": sum(winning_trades) / abs(sum(losing_trades)) if losing_trades else float('inf'),
            "average_trade_duration": self._calculate_average_trade_duration(trades)
        }
    
    def _calculate_average_trade_duration(self, trades: List[Dict]) -> float:
        """Calcular duración promedio de trades"""
        durations = []
        for trade in trades:
            if trade.get("entry_time") and trade.get("exit_time"):
                try:
                    entry = datetime.fromisoformat(trade["entry_time"].replace('Z', '+00:00'))
                    exit = datetime.fromisoformat(trade["exit_time"].replace('Z', '+00:00'))
                    duration = (exit - entry).total_seconds() / 3600  # horas
                    durations.append(duration)
                except:
                    continue
        
        return np.mean(durations) if durations else 0
    
    def _calculate_risk_metrics_from_trades(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calcular métricas de riesgo desde trades"""
        if not trades:
            return {}
        
        profits = [t.get("pnl", 0) for t in trades]
        
        # Calcular métricas básicas
        total_return = sum(profits)
        returns_std = np.std(profits) if len(profits) > 1 else 0
        
        # Sharpe ratio usando función personalizada
        returns_series = pd.Series(profits) if profits else pd.Series([])
        sharpe = self.calculate_sharpe_ratio(returns_series)
        
        # Sortino ratio (usando solo desviación de pérdidas)
        negative_returns = [p for p in profits if p < 0]
        downside_std = np.std(negative_returns) if len(negative_returns) > 1 else 0
        sortino = total_return / downside_std if downside_std > 0 else 0
        
        return {
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "volatility": returns_std,
            "downside_volatility": downside_std,
            "skewness": float(pd.Series(profits).skew()) if len(profits) > 2 else 0,
            "kurtosis": float(pd.Series(profits).kurtosis()) if len(profits) > 3 else 0
        }
    
    def _calculate_monthly_performance(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calcular performance mensual"""
        monthly_pnl = {}
        
        for trade in trades:
            if trade.get("exit_time"):
                try:
                    exit_date = datetime.fromisoformat(trade["exit_time"].replace('Z', '+00:00'))
                    month_key = exit_date.strftime("%Y-%m")
                    
                    if month_key not in monthly_pnl:
                        monthly_pnl[month_key] = 0
                    
                    monthly_pnl[month_key] += trade.get("pnl", 0)
                except:
                    continue
        
        if not monthly_pnl:
            return {"error": "No se pudo calcular performance mensual"}
        
        monthly_returns = list(monthly_pnl.values())
        positive_months = len([r for r in monthly_returns if r > 0])
        
        return {
            "monthly_pnl": monthly_pnl,
            "positive_months": positive_months,
            "negative_months": len(monthly_returns) - positive_months,
            "best_month": max(monthly_returns),
            "worst_month": min(monthly_returns),
            "average_monthly_return": np.mean(monthly_returns),
            "monthly_volatility": np.std(monthly_returns)
        }
    
    def _analyze_drawdowns(self, trades: List[Dict]) -> Dict[str, Any]:
        """Analizar drawdowns"""
        if not trades:
            return {}
        
        # Calcular curva de equity
        cumulative_pnl = 0
        equity_curve = [0]
        
        for trade in trades:
            cumulative_pnl += trade.get("pnl", 0)
            equity_curve.append(cumulative_pnl)
        
        # Calcular drawdowns
        peak = equity_curve[0]
        drawdowns = []
        current_drawdown = 0
        
        for value in equity_curve:
            if value > peak:
                peak = value
                if current_drawdown < 0:
                    drawdowns.append(abs(current_drawdown))
                current_drawdown = 0
            else:
                current_drawdown = value - peak
        
        if current_drawdown < 0:
            drawdowns.append(abs(current_drawdown))
        
        return {
            "max_drawdown": max(drawdowns) if drawdowns else 0,
            "average_drawdown": np.mean(drawdowns) if drawdowns else 0,
            "drawdown_periods": len(drawdowns),
            "current_drawdown": abs(current_drawdown),
            "recovery_factor": equity_curve[-1] / max(drawdowns) if drawdowns and max(drawdowns) > 0 else 0
        }
    
    def _analyze_performance_attribution(self, trades: List[Dict]) -> Dict[str, Any]:
        """Analizar atribución de performance"""
        if not trades:
            return {}
        
        # Agrupar por diferentes criterios
        by_hour = {}
        by_day_of_week = {}
        by_trade_size = {"small": [], "medium": [], "large": []}
        
        for trade in trades:
            pnl = trade.get("pnl", 0)
            
            # Por hora
            if trade.get("entry_time"):
                try:
                    entry_time = datetime.fromisoformat(trade["entry_time"].replace('Z', '+00:00'))
                    hour = entry_time.hour
                    if hour not in by_hour:
                        by_hour[hour] = []
                    by_hour[hour].append(pnl)
                    
                    # Por día de la semana
                    day_of_week = entry_time.weekday()
                    if day_of_week not in by_day_of_week:
                        by_day_of_week[day_of_week] = []
                    by_day_of_week[day_of_week].append(pnl)
                except:
                    continue
            
            # Por tamaño de trade
            trade_size = abs(trade.get("quantity", 0))
            if trade_size < 0.01:
                by_trade_size["small"].append(pnl)
            elif trade_size < 0.1:
                by_trade_size["medium"].append(pnl)
            else:
                by_trade_size["large"].append(pnl)
        
        return {
            "by_hour": {hour: np.mean(pnls) for hour, pnls in by_hour.items()},
            "by_day_of_week": {day: np.mean(pnls) for day, pnls in by_day_of_week.items()},
            "by_trade_size": {size: np.mean(pnls) if pnls else 0 for size, pnls in by_trade_size.items()},
            "best_hour": max(by_hour.items(), key=lambda x: np.mean(x[1]))[0] if by_hour else None,
            "best_day": max(by_day_of_week.items(), key=lambda x: np.mean(x[1]))[0] if by_day_of_week else None
        }
    
    def _generate_performance_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones basadas en análisis de performance"""
        recommendations = []
        
        trade_analysis = analysis.get("trade_analysis", {})
        risk_metrics = analysis.get("risk_metrics", {})
        drawdown_analysis = analysis.get("drawdown_analysis", {})
        
        # Recomendaciones basadas en win rate
        win_rate = trade_analysis.get("win_rate", 0)
        if win_rate < 0.4:
            recommendations.append("Win rate bajo (<40%) - considerar ajustar criterios de entrada")
        elif win_rate > 0.8:
            recommendations.append("Win rate muy alto (>80%) - verificar si hay overfitting")
        
        # Recomendaciones basadas en profit factor
        profit_factor = trade_analysis.get("profit_factor", 0)
        if profit_factor < 1.2:
            recommendations.append("Profit factor bajo (<1.2) - mejorar relación riesgo/beneficio")
        
        # Recomendaciones basadas en Sharpe ratio
        sharpe = risk_metrics.get("sharpe_ratio", 0)
        if sharpe < 1.0:
            recommendations.append("Sharpe ratio bajo (<1.0) - considerar reducir volatilidad")
        
        # Recomendaciones basadas en drawdown
        max_drawdown = drawdown_analysis.get("max_drawdown", 0)
        if max_drawdown > 0.2:  # 20%
            recommendations.append("Drawdown alto (>20%) - implementar mejor gestión de riesgo")
        
        if not recommendations:
            recommendations.append("Performance dentro de parámetros aceptables")
        
        return recommendations
    
    async def _save_optimization_results(self, optimization_id: str, results: Dict[str, Any]):
        """Guardar resultados de optimización en base de datos"""
        try:
            backtest_data = {
                "backtest_id": optimization_id,
                "strategy_name": results.get("strategy_name", "unknown"),
                "symbol": results.get("symbol", "unknown"),
                "start_date": datetime.strptime("2023-01-01", "%Y-%m-%d"),
                "end_date": datetime.strptime("2024-01-01", "%Y-%m-%d"),
                "initial_capital": 1000.0,
                "final_capital": 1000.0 + results.get("best_value", 0),
                "total_return": results.get("best_value", 0),
                "parameters": results.get("best_parameters", {}),
                "detailed_results": results
            }
            
            await DatabaseManager.save_backtest_result(backtest_data)
            self.logger.info(f"Resultados de optimización guardados: {optimization_id}")
            
        except Exception as e:
            self.logger.error(f"Error guardando resultados de optimización: {e}")
    
    async def _periodic_tasks(self):
        """Tareas periódicas del agente optimizador"""
        # Limpiar optimizaciones completadas antiguas
        current_time = datetime.utcnow()
        completed_to_remove = []
        
        for opt_id, opt_info in self.current_optimizations.items():
            if opt_info.get("status") == "completed":
                end_time = opt_info.get("end_time", current_time)
                if (current_time - end_time).total_seconds() > 3600:  # 1 hora
                    completed_to_remove.append(opt_id)
        
        for opt_id in completed_to_remove:
            del self.current_optimizations[opt_id]
        
        await asyncio.sleep(0.1)