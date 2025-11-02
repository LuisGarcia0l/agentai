"""
Agent Manager - Coordinador central de todos los agentes del sistema
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

from backend.agents.base_agent import BaseAgent, AgentTask
from backend.agents.research_agent import ResearchAgent
from backend.agents.trading_agent import TradingAgent
from backend.agents.risk_agent import RiskAgent
from backend.agents.optimizer_agent import OptimizerAgent
from backend.core.config import settings
from backend.core.database import DatabaseManager

class AgentManager:
    """
    Manager central que coordina todos los agentes del sistema
    
    Responsabilidades:
    - Inicializar y gestionar el ciclo de vida de los agentes
    - Coordinar comunicación entre agentes
    - Distribuir tareas según prioridades
    - Monitorear estado y performance de agentes
    - Implementar workflows de trading automatizado
    """
    
    def __init__(self):
        self.logger = logging.getLogger("agents.manager")
        self.agents: Dict[str, BaseAgent] = {}
        self.is_running = False
        self.workflows = {}
        self.task_queue = asyncio.Queue()
        self.coordination_rules = self._setup_coordination_rules()
        
    async def initialize(self):
        """Inicializar todos los agentes"""
        try:
            self.logger.info("🤖 Inicializando Agent Manager...")
            
            # Crear instancias de agentes
            self.agents = {
                "research": ResearchAgent(),
                "trading": TradingAgent(),
                "risk": RiskAgent(),
                "optimizer": OptimizerAgent()
            }
            
            # Inicializar cada agente
            initialization_results = {}
            for name, agent in self.agents.items():
                try:
                    success = await agent.initialize()
                    initialization_results[name] = success
                    if success:
                        await agent.start()
                        self.logger.info(f"✅ Agente {name} inicializado y iniciado")
                    else:
                        self.logger.error(f"❌ Error inicializando agente {name}")
                except Exception as e:
                    self.logger.error(f"❌ Error crítico inicializando agente {name}: {e}")
                    initialization_results[name] = False
            
            # Verificar que al menos los agentes críticos estén funcionando
            critical_agents = ["research", "trading", "risk"]
            critical_failures = [name for name in critical_agents if not initialization_results.get(name, False)]
            
            if critical_failures:
                raise Exception(f"Agentes críticos fallaron: {critical_failures}")
            
            self.is_running = True
            self.logger.info("✅ Agent Manager inicializado correctamente")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando Agent Manager: {e}")
            raise
    
    async def shutdown(self):
        """Cerrar todos los agentes"""
        self.logger.info("🛑 Cerrando Agent Manager...")
        
        self.is_running = False
        
        # Detener todos los agentes
        for name, agent in self.agents.items():
            try:
                await agent.stop()
                self.logger.info(f"✅ Agente {name} detenido")
            except Exception as e:
                self.logger.error(f"❌ Error deteniendo agente {name}: {e}")
        
        self.logger.info("✅ Agent Manager cerrado")
    
    def _setup_coordination_rules(self) -> Dict[str, Any]:
        """Configurar reglas de coordinación entre agentes"""
        return {
            "trading_workflow": {
                "sequence": ["research", "risk", "trading"],
                "conditions": {
                    "research": {"min_confidence": 0.6},
                    "risk": {"max_risk_score": 70},
                    "trading": {"max_position_size": settings.MAX_POSITION_SIZE}
                }
            },
            "optimization_workflow": {
                "sequence": ["research", "optimizer", "risk"],
                "conditions": {
                    "research": {"min_data_points": 100},
                    "optimizer": {"min_trials": 50},
                    "risk": {"max_drawdown": settings.MAX_DRAWDOWN}
                }
            },
            "risk_monitoring": {
                "triggers": ["portfolio_update", "market_volatility", "drawdown_alert"],
                "response_agents": ["risk", "trading"]
            }
        }
    
    async def start_monitoring(self):
        """Iniciar monitoreo continuo del sistema"""
        if not self.is_running:
            return
        
        self.logger.info("🔄 Iniciando monitoreo continuo...")
        
        # Iniciar tareas de monitoreo en background
        asyncio.create_task(self._coordination_loop())
        asyncio.create_task(self._health_monitoring())
        asyncio.create_task(self._automated_workflows())
        
    async def _coordination_loop(self):
        """Loop principal de coordinación"""
        while self.is_running:
            try:
                # Procesar tareas de coordinación
                await self._process_coordination_tasks()
                
                # Verificar workflows activos
                await self._check_active_workflows()
                
                # Pausa entre iteraciones
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error en loop de coordinación: {e}")
                await asyncio.sleep(10)
    
    async def _health_monitoring(self):
        """Monitoreo de salud de agentes"""
        while self.is_running:
            try:
                # Verificar estado de cada agente
                for name, agent in self.agents.items():
                    status = agent.get_status()
                    
                    # Alertar si un agente está en error
                    if status["status"] == "error":
                        self.logger.warning(f"⚠️ Agente {name} en estado de error")
                        # Intentar reiniciar agente si es crítico
                        if name in ["research", "trading", "risk"]:
                            await self._restart_agent(name)
                    
                    # Verificar si un agente está sobrecargado
                    if status["queue_size"] > 50:
                        self.logger.warning(f"⚠️ Agente {name} sobrecargado: {status['queue_size']} tareas")
                
                await asyncio.sleep(30)  # Verificar cada 30 segundos
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo de salud: {e}")
                await asyncio.sleep(60)
    
    async def _automated_workflows(self):
        """Ejecutar workflows automatizados"""
        while self.is_running:
            try:
                # Workflow de análisis de mercado cada hora
                await self._execute_market_analysis_workflow()
                
                # Workflow de optimización diaria
                if datetime.utcnow().hour == 2:  # 2 AM
                    await self._execute_daily_optimization_workflow()
                
                # Workflow de reporte semanal
                if datetime.utcnow().weekday() == 0 and datetime.utcnow().hour == 8:  # Lunes 8 AM
                    await self._execute_weekly_report_workflow()
                
                await asyncio.sleep(3600)  # Verificar cada hora
                
            except Exception as e:
                self.logger.error(f"Error en workflows automatizados: {e}")
                await asyncio.sleep(3600)
    
    async def _restart_agent(self, agent_name: str):
        """Reiniciar un agente específico"""
        try:
            self.logger.info(f"🔄 Reiniciando agente {agent_name}...")
            
            agent = self.agents.get(agent_name)
            if not agent:
                return False
            
            # Detener agente
            await agent.stop()
            
            # Reinicializar
            success = await agent.initialize()
            if success:
                await agent.start()
                self.logger.info(f"✅ Agente {agent_name} reiniciado exitosamente")
                return True
            else:
                self.logger.error(f"❌ Error reiniciando agente {agent_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error reiniciando agente {agent_name}: {e}")
            return False
    
    # Métodos públicos para interactuar con agentes
    
    async def execute_trading_workflow(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutar workflow completo de trading
        
        Args:
            parameters: Parámetros del trade (symbol, strategy, etc.)
            
        Returns:
            Resultado del workflow
        """
        workflow_id = f"trading_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            self.logger.info(f"🚀 Ejecutando workflow de trading: {workflow_id}")
            
            workflow_result = {
                "workflow_id": workflow_id,
                "status": "running",
                "steps": {},
                "final_result": None
            }
            
            # Paso 1: Análisis de investigación
            self.logger.info("📊 Paso 1: Análisis de mercado")
            research_task = AgentTask(
                task_id=f"{workflow_id}_research",
                task_type="technical_analysis",
                parameters={
                    "symbol": parameters.get("symbol", settings.DEFAULT_TRADING_PAIR),
                    "timeframe": parameters.get("timeframe", "1h"),
                    "periods": parameters.get("periods", 100)
                }
            )
            
            research_agent = self.agents["research"]
            await research_agent.add_task(research_task)
            
            # Esperar resultado (con timeout)
            research_result = await self._wait_for_task_completion(research_agent, research_task.task_id, timeout=60)
            workflow_result["steps"]["research"] = research_result
            
            if not research_result or research_result.get("signals", {}).get("overall_signal") == "neutral":
                workflow_result["status"] = "aborted"
                workflow_result["reason"] = "Señal de investigación neutral o insuficiente"
                return workflow_result
            
            # Paso 2: Evaluación de riesgo
            self.logger.info("⚠️ Paso 2: Evaluación de riesgo")
            
            # Obtener estado actual del portafolio
            portfolio_status = await self._get_current_portfolio_status()
            
            risk_task = AgentTask(
                task_id=f"{workflow_id}_risk",
                task_type="check_trade_risk",
                parameters={
                    "symbol": parameters.get("symbol"),
                    "side": "BUY" if research_result.get("signals", {}).get("overall_signal") == "buy" else "SELL",
                    "quantity": parameters.get("quantity", 0.01),
                    "current_balance": portfolio_status.get("current_balance", 1000.0),
                    "active_positions": portfolio_status.get("active_positions", {})
                }
            )
            
            risk_agent = self.agents["risk"]
            await risk_agent.add_task(risk_task)
            
            risk_result = await self._wait_for_task_completion(risk_agent, risk_task.task_id, timeout=30)
            workflow_result["steps"]["risk"] = risk_result
            
            if not risk_result or not risk_result.get("approved", False):
                workflow_result["status"] = "rejected"
                workflow_result["reason"] = f"Trade rechazado por riesgo: {risk_result.get('reason', 'Unknown')}"
                return workflow_result
            
            # Paso 3: Ejecución de trading
            self.logger.info("💰 Paso 3: Ejecución de trade")
            
            trading_task = AgentTask(
                task_id=f"{workflow_id}_trading",
                task_type="execute_trade",
                parameters={
                    "symbol": parameters.get("symbol"),
                    "side": "BUY" if research_result.get("signals", {}).get("overall_signal") == "buy" else "SELL",
                    "quantity": parameters.get("quantity", 0.01),
                    "order_type": parameters.get("order_type", "MARKET"),
                    "strategy": parameters.get("strategy", "automated"),
                    "stop_loss": parameters.get("stop_loss"),
                    "take_profit": parameters.get("take_profit")
                }
            )
            
            trading_agent = self.agents["trading"]
            await trading_agent.add_task(trading_task)
            
            trading_result = await self._wait_for_task_completion(trading_agent, trading_task.task_id, timeout=60)
            workflow_result["steps"]["trading"] = trading_result
            
            if trading_result and trading_result.get("success", False):
                workflow_result["status"] = "completed"
                workflow_result["final_result"] = trading_result
                self.logger.info(f"✅ Workflow de trading completado: {workflow_id}")
            else:
                workflow_result["status"] = "failed"
                workflow_result["reason"] = f"Error ejecutando trade: {trading_result.get('error', 'Unknown')}"
            
            return workflow_result
            
        except Exception as e:
            self.logger.error(f"Error en workflow de trading: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e)
            }
    
    async def execute_research_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar análisis de investigación"""
        try:
            research_agent = self.agents["research"]
            
            task = AgentTask(
                task_id=f"research_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                task_type=parameters.get("analysis_type", "technical_analysis"),
                parameters=parameters
            )
            
            await research_agent.add_task(task)
            result = await self._wait_for_task_completion(research_agent, task.task_id, timeout=120)
            
            return {
                "success": True,
                "task_id": task.task_id,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis de investigación: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_optimization(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar optimización de estrategia"""
        try:
            optimizer_agent = self.agents["optimizer"]
            
            task = AgentTask(
                task_id=f"optimization_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                task_type="optimize_strategy",
                parameters=parameters
            )
            
            await optimizer_agent.add_task(task)
            
            # La optimización puede tomar mucho tiempo
            result = await self._wait_for_task_completion(optimizer_agent, task.task_id, timeout=3600)
            
            return {
                "success": True,
                "task_id": task.task_id,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error en optimización: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_portfolio_risk_assessment(self) -> Dict[str, Any]:
        """Obtener evaluación de riesgo del portafolio"""
        try:
            # Obtener estado actual del portafolio
            portfolio_status = await self._get_current_portfolio_status()
            
            risk_agent = self.agents["risk"]
            
            task = AgentTask(
                task_id=f"risk_assessment_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                task_type="assess_portfolio_risk",
                parameters={"portfolio": portfolio_status}
            )
            
            await risk_agent.add_task(task)
            result = await self._wait_for_task_completion(risk_agent, task.task_id, timeout=60)
            
            return {
                "success": True,
                "assessment": result
            }
            
        except Exception as e:
            self.logger.error(f"Error en evaluación de riesgo: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_current_portfolio_status(self) -> Dict[str, Any]:
        """Obtener estado actual del portafolio"""
        try:
            trading_agent = self.agents["trading"]
            
            task = AgentTask(
                task_id=f"portfolio_status_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                task_type="get_portfolio_status",
                parameters={}
            )
            
            await trading_agent.add_task(task)
            result = await self._wait_for_task_completion(trading_agent, task.task_id, timeout=30)
            
            if result and result.get("success", False):
                return result.get("portfolio", {})
            else:
                return {
                    "current_balance": 1000.0,
                    "active_positions": {},
                    "total_portfolio_value": 1000.0
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del portafolio: {e}")
            return {
                "current_balance": 1000.0,
                "active_positions": {},
                "total_portfolio_value": 1000.0
            }
    
    async def _wait_for_task_completion(self, agent: BaseAgent, task_id: str, timeout: int = 60) -> Optional[Any]:
        """Esperar a que se complete una tarea específica"""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            # Verificar si la tarea está completada
            if agent.current_task is None or agent.current_task.task_id != task_id:
                # La tarea ya no está en ejecución, buscar resultado
                # En una implementación real, esto se haría a través de una base de datos
                # o sistema de mensajería. Por simplicidad, asumimos que está completada.
                break
            
            await asyncio.sleep(1)
        
        # En una implementación real, aquí obtendríamos el resultado de la base de datos
        # Por ahora, retornamos None para indicar que necesitamos implementar el sistema de resultados
        return None
    
    async def _execute_market_analysis_workflow(self):
        """Workflow automatizado de análisis de mercado"""
        try:
            self.logger.info("📊 Ejecutando análisis de mercado automatizado")
            
            # Analizar principales criptomonedas
            symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]
            
            research_agent = self.agents["research"]
            
            task = AgentTask(
                task_id=f"market_scan_{datetime.utcnow().strftime('%Y%m%d_%H')}",
                task_type="scan_opportunities",
                parameters={"symbols": symbols}
            )
            
            await research_agent.add_task(task)
            
        except Exception as e:
            self.logger.error(f"Error en análisis de mercado automatizado: {e}")
    
    async def _execute_daily_optimization_workflow(self):
        """Workflow diario de optimización"""
        try:
            self.logger.info("🔧 Ejecutando optimización diaria")
            
            # Optimizar estrategia principal
            optimizer_agent = self.agents["optimizer"]
            
            task = AgentTask(
                task_id=f"daily_optimization_{datetime.utcnow().strftime('%Y%m%d')}",
                task_type="optimize_strategy",
                parameters={
                    "strategy_name": "rsi_macd_strategy",
                    "symbol": settings.DEFAULT_TRADING_PAIR,
                    "method": "bayesian",
                    "n_trials": 50
                }
            )
            
            await optimizer_agent.add_task(task)
            
        except Exception as e:
            self.logger.error(f"Error en optimización diaria: {e}")
    
    async def _execute_weekly_report_workflow(self):
        """Workflow semanal de reportes"""
        try:
            self.logger.info("📈 Generando reporte semanal")
            
            # Generar reporte de riesgo
            risk_agent = self.agents["risk"]
            
            portfolio_status = await self._get_current_portfolio_status()
            
            task = AgentTask(
                task_id=f"weekly_report_{datetime.utcnow().strftime('%Y%m%d')}",
                task_type="generate_risk_report",
                parameters={"portfolio": portfolio_status}
            )
            
            await risk_agent.add_task(task)
            
        except Exception as e:
            self.logger.error(f"Error en reporte semanal: {e}")
    
    async def _process_coordination_tasks(self):
        """Procesar tareas de coordinación entre agentes"""
        # Implementar lógica de coordinación específica
        pass
    
    async def _check_active_workflows(self):
        """Verificar workflows activos"""
        # Implementar verificación de workflows en progreso
        pass
    
    # Métodos de información y estado
    
    def get_active_agents_count(self) -> int:
        """Obtener número de agentes activos"""
        return len([agent for agent in self.agents.values() if agent.is_running])
    
    async def get_agents_status(self) -> Dict[str, Any]:
        """Obtener estado de todos los agentes"""
        status = {}
        
        for name, agent in self.agents.items():
            status[name] = agent.get_status()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_agents": len(self.agents),
            "active_agents": self.get_active_agents_count(),
            "agents": status,
            "manager_status": {
                "is_running": self.is_running,
                "workflows_active": len(self.workflows)
            }
        }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del sistema"""
        agents_status = await self.get_agents_status()
        
        # Calcular métricas agregadas
        total_tasks_completed = sum(
            agent_status["stats"]["tasks_completed"] 
            for agent_status in agents_status["agents"].values()
        )
        
        total_tasks_failed = sum(
            agent_status["stats"]["tasks_failed"] 
            for agent_status in agents_status["agents"].values()
        )
        
        total_execution_time = sum(
            agent_status["stats"]["total_execution_time"] 
            for agent_status in agents_status["agents"].values()
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_uptime": self.is_running,
            "agents_status": agents_status,
            "performance_metrics": {
                "total_tasks_completed": total_tasks_completed,
                "total_tasks_failed": total_tasks_failed,
                "success_rate": total_tasks_completed / (total_tasks_completed + total_tasks_failed) if (total_tasks_completed + total_tasks_failed) > 0 else 0,
                "total_execution_time": total_execution_time,
                "average_task_time": total_execution_time / total_tasks_completed if total_tasks_completed > 0 else 0
            }
        }