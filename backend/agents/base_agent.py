"""
Agente base para el sistema AutoDev Trading Studio
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from backend.core.config import settings
from backend.core.database import DatabaseManager

class AgentStatus(Enum):
    """Estados posibles de un agente"""
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"
    STOPPED = "stopped"

@dataclass
class AgentTask:
    """Tarea para un agente"""
    task_id: str
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 1
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class BaseAgent(ABC):
    """Clase base para todos los agentes del sistema"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"agents.{name}")
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        self.current_task: Optional[AgentTask] = None
        self.execution_stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "last_activity": None
        }
        
    async def initialize(self) -> bool:
        """
        Inicializar el agente
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.logger.info(f"🤖 Inicializando agente {self.name}")
            
            # Llamar inicialización específica del agente
            await self._initialize_agent()
            
            self.logger.info(f"✅ Agente {self.name} inicializado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando agente {self.name}: {e}")
            self.status = AgentStatus.ERROR
            return False
    
    async def start(self):
        """Iniciar el agente"""
        if self.is_running:
            self.logger.warning(f"Agente {self.name} ya está ejecutándose")
            return
            
        self.is_running = True
        self.status = AgentStatus.IDLE
        self.logger.info(f"🚀 Iniciando agente {self.name}")
        
        # Iniciar loop principal del agente
        asyncio.create_task(self._main_loop())
    
    async def stop(self):
        """Detener el agente"""
        self.logger.info(f"🛑 Deteniendo agente {self.name}")
        self.is_running = False
        self.status = AgentStatus.STOPPED
        
        # Limpiar tareas pendientes
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
    
    async def add_task(self, task: AgentTask):
        """
        Agregar tarea a la cola del agente
        
        Args:
            task: Tarea a ejecutar
        """
        await self.task_queue.put(task)
        self.logger.debug(f"Tarea {task.task_id} agregada a la cola de {self.name}")
    
    async def _main_loop(self):
        """Loop principal del agente"""
        while self.is_running:
            try:
                # Esperar por tareas con timeout
                try:
                    task = await asyncio.wait_for(
                        self.task_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    # Ejecutar tareas periódicas si no hay tareas en cola
                    await self._periodic_tasks()
                    continue
                
                # Ejecutar tarea
                await self._execute_task(task)
                
            except Exception as e:
                self.logger.error(f"Error en loop principal de {self.name}: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: AgentTask):
        """
        Ejecutar una tarea específica
        
        Args:
            task: Tarea a ejecutar
        """
        start_time = datetime.utcnow()
        self.current_task = task
        self.status = AgentStatus.WORKING
        
        try:
            self.logger.info(f"🔄 Ejecutando tarea {task.task_id} ({task.task_type})")
            
            # Ejecutar la tarea específica del agente
            result = await self._process_task(task)
            
            # Calcular tiempo de ejecución
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Actualizar estadísticas
            self.execution_stats["tasks_completed"] += 1
            self.execution_stats["total_execution_time"] += execution_time
            self.execution_stats["last_activity"] = datetime.utcnow()
            
            # Registrar actividad en base de datos
            await self._log_activity(task, result, execution_time, "success")
            
            self.logger.info(f"✅ Tarea {task.task_id} completada en {execution_time:.2f}s")
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Actualizar estadísticas de error
            self.execution_stats["tasks_failed"] += 1
            self.execution_stats["total_execution_time"] += execution_time
            
            # Registrar error
            await self._log_activity(task, None, execution_time, "error", str(e))
            
            self.logger.error(f"❌ Error ejecutando tarea {task.task_id}: {e}")
            
        finally:
            self.current_task = None
            self.status = AgentStatus.IDLE
    
    async def _log_activity(self, task: AgentTask, result: Any, execution_time: float, 
                          status: str, error_message: str = None):
        """Registrar actividad del agente en base de datos"""
        try:
            activity_data = {
                "agent_name": self.name,
                "activity_type": task.task_type,
                "description": f"Ejecutar tarea {task.task_id}",
                "input_data": task.parameters,
                "output_data": result if result is not None else {},
                "execution_time": execution_time,
                "status": status,
                "error_message": error_message
            }
            
            await DatabaseManager.log_agent_activity(activity_data)
            
        except Exception as e:
            self.logger.error(f"Error registrando actividad: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual del agente
        
        Returns:
            Diccionario con información del estado
        """
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "is_running": self.is_running,
            "current_task": self.current_task.task_id if self.current_task else None,
            "queue_size": self.task_queue.qsize(),
            "stats": self.execution_stats
        }
    
    # Métodos abstractos que deben implementar los agentes específicos
    
    @abstractmethod
    async def _initialize_agent(self):
        """Inicialización específica del agente"""
        pass
    
    @abstractmethod
    async def _process_task(self, task: AgentTask) -> Any:
        """
        Procesar una tarea específica
        
        Args:
            task: Tarea a procesar
            
        Returns:
            Resultado de la tarea
        """
        pass
    
    async def _periodic_tasks(self):
        """Tareas periódicas del agente (ejecutadas cuando no hay tareas en cola)"""
        # Implementación por defecto: no hacer nada
        await asyncio.sleep(0.1)
    
    # Métodos de utilidad
    
    def create_task(self, task_type: str, parameters: Dict[str, Any], 
                   priority: int = 1) -> AgentTask:
        """
        Crear una nueva tarea
        
        Args:
            task_type: Tipo de tarea
            parameters: Parámetros de la tarea
            priority: Prioridad (1 = alta, 5 = baja)
            
        Returns:
            Nueva tarea
        """
        task_id = f"{self.name}_{task_type}_{datetime.utcnow().timestamp()}"
        return AgentTask(
            task_id=task_id,
            task_type=task_type,
            parameters=parameters,
            priority=priority
        )