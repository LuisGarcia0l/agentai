"""
Gestor de WebSocket para comunicación en tiempo real
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Set
from fastapi import WebSocket

class WebSocketManager:
    """
    Gestor de conexiones WebSocket para comunicación en tiempo real
    
    Funcionalidades:
    - Gestión de conexiones múltiples
    - Broadcast de mensajes
    - Canales temáticos
    - Heartbeat para mantener conexiones
    """
    
    def __init__(self):
        self.logger = logging.getLogger("services.websocket")
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        self.channels: Dict[str, Set[WebSocket]] = {}
        self.heartbeat_task = None
        
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        """Conectar un nuevo cliente WebSocket"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            # Guardar información del cliente
            self.connection_info[websocket] = {
                "connected_at": datetime.utcnow(),
                "client_info": client_info or {},
                "subscribed_channels": set(),
                "last_heartbeat": datetime.utcnow()
            }
            
            self.logger.info(f"✅ Nueva conexión WebSocket: {len(self.active_connections)} activas")
            
            # Enviar mensaje de bienvenida
            await self.send_personal_message({
                "type": "connection_established",
                "message": "Conectado al AutoDev Trading Studio",
                "timestamp": datetime.utcnow().isoformat(),
                "server_time": datetime.utcnow().isoformat()
            }, websocket)
            
            # Iniciar heartbeat si es la primera conexión
            if len(self.active_connections) == 1 and not self.heartbeat_task:
                self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                
        except Exception as e:
            self.logger.error(f"Error conectando WebSocket: {e}")
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Desconectar un cliente WebSocket"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            # Remover de canales
            if websocket in self.connection_info:
                subscribed_channels = self.connection_info[websocket].get("subscribed_channels", set())
                for channel in subscribed_channels:
                    if channel in self.channels and websocket in self.channels[channel]:
                        self.channels[channel].remove(websocket)
                
                del self.connection_info[websocket]
            
            self.logger.info(f"❌ Conexión WebSocket desconectada: {len(self.active_connections)} activas")
            
            # Detener heartbeat si no hay conexiones
            if len(self.active_connections) == 0 and self.heartbeat_task:
                self.heartbeat_task.cancel()
                self.heartbeat_task = None
                
        except Exception as e:
            self.logger.error(f"Error desconectando WebSocket: {e}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Enviar mensaje a un cliente específico"""
        try:
            if websocket in self.active_connections:
                message_str = json.dumps(message, default=str)
                await websocket.send_text(message_str)
                
        except Exception as e:
            self.logger.error(f"Error enviando mensaje personal: {e}")
            # Remover conexión si está rota
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any], exclude: WebSocket = None):
        """Enviar mensaje a todas las conexiones activas"""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message, default=str)
        disconnected = []
        
        for connection in self.active_connections:
            if connection != exclude:
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    self.logger.error(f"Error enviando broadcast: {e}")
                    disconnected.append(connection)
        
        # Limpiar conexiones rotas
        for connection in disconnected:
            self.disconnect(connection)
    
    async def subscribe_to_channel(self, websocket: WebSocket, channel: str):
        """Suscribir cliente a un canal específico"""
        try:
            if channel not in self.channels:
                self.channels[channel] = set()
            
            self.channels[channel].add(websocket)
            
            if websocket in self.connection_info:
                self.connection_info[websocket]["subscribed_channels"].add(channel)
            
            await self.send_personal_message({
                "type": "channel_subscribed",
                "channel": channel,
                "message": f"Suscrito al canal {channel}",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
            
            self.logger.debug(f"Cliente suscrito al canal {channel}")
            
        except Exception as e:
            self.logger.error(f"Error suscribiendo a canal {channel}: {e}")
    
    async def unsubscribe_from_channel(self, websocket: WebSocket, channel: str):
        """Desuscribir cliente de un canal"""
        try:
            if channel in self.channels and websocket in self.channels[channel]:
                self.channels[channel].remove(websocket)
            
            if websocket in self.connection_info:
                self.connection_info[websocket]["subscribed_channels"].discard(channel)
            
            await self.send_personal_message({
                "type": "channel_unsubscribed",
                "channel": channel,
                "message": f"Desuscrito del canal {channel}",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
            
            self.logger.debug(f"Cliente desuscrito del canal {channel}")
            
        except Exception as e:
            self.logger.error(f"Error desuscribiendo del canal {channel}: {e}")
    
    async def send_to_channel(self, channel: str, message: Dict[str, Any]):
        """Enviar mensaje a todos los suscriptores de un canal"""
        if channel not in self.channels:
            return
        
        message_str = json.dumps(message, default=str)
        disconnected = []
        
        for connection in self.channels[channel].copy():
            try:
                await connection.send_text(message_str)
            except Exception as e:
                self.logger.error(f"Error enviando a canal {channel}: {e}")
                disconnected.append(connection)
        
        # Limpiar conexiones rotas
        for connection in disconnected:
            self.disconnect(connection)
    
    async def _heartbeat_loop(self):
        """Loop de heartbeat para mantener conexiones activas"""
        while self.active_connections:
            try:
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_connections": len(self.active_connections)
                }
                
                await self.broadcast(heartbeat_message)
                await asyncio.sleep(30)  # Heartbeat cada 30 segundos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en heartbeat loop: {e}")
                await asyncio.sleep(30)
    
    # Métodos específicos para el sistema de trading
    
    async def send_trade_update(self, trade_data: Dict[str, Any]):
        """Enviar actualización de trade"""
        message = {
            "type": "trade_update",
            "data": trade_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_channel("trades", message)
    
    async def send_portfolio_update(self, portfolio_data: Dict[str, Any]):
        """Enviar actualización de portafolio"""
        message = {
            "type": "portfolio_update",
            "data": portfolio_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_channel("portfolio", message)
    
    async def send_market_data(self, market_data: Dict[str, Any]):
        """Enviar datos de mercado"""
        message = {
            "type": "market_data",
            "data": market_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_channel("market", message)
    
    async def send_risk_alert(self, alert_data: Dict[str, Any]):
        """Enviar alerta de riesgo"""
        message = {
            "type": "risk_alert",
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_channel("alerts", message)
        # También enviar a todos los clientes (alta prioridad)
        await self.broadcast(message)
    
    async def send_agent_status(self, agent_status: Dict[str, Any]):
        """Enviar estado de agentes"""
        message = {
            "type": "agent_status",
            "data": agent_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_channel("agents", message)
    
    async def send_backtest_progress(self, backtest_data: Dict[str, Any]):
        """Enviar progreso de backtesting"""
        message = {
            "type": "backtest_progress",
            "data": backtest_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_channel("backtesting", message)
    
    async def send_optimization_progress(self, optimization_data: Dict[str, Any]):
        """Enviar progreso de optimización"""
        message = {
            "type": "optimization_progress",
            "data": optimization_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_channel("optimization", message)
    
    async def handle_client_message(self, websocket: WebSocket, message: str):
        """Manejar mensaje del cliente"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                channel = data.get("channel")
                if channel:
                    await self.subscribe_to_channel(websocket, channel)
            
            elif message_type == "unsubscribe":
                channel = data.get("channel")
                if channel:
                    await self.unsubscribe_from_channel(websocket, channel)
            
            elif message_type == "ping":
                await self.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
            
            elif message_type == "get_status":
                status = await self.get_connection_status()
                await self.send_personal_message({
                    "type": "status_response",
                    "data": status,
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
            
            else:
                await self.send_personal_message({
                    "type": "error",
                    "message": f"Tipo de mensaje no reconocido: {message_type}",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
            
            # Actualizar último heartbeat
            if websocket in self.connection_info:
                self.connection_info[websocket]["last_heartbeat"] = datetime.utcnow()
                
        except json.JSONDecodeError:
            await self.send_personal_message({
                "type": "error",
                "message": "Formato de mensaje inválido",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
        except Exception as e:
            self.logger.error(f"Error manejando mensaje del cliente: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": "Error procesando mensaje",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Obtener estado de las conexiones"""
        try:
            channels_info = {}
            for channel, connections in self.channels.items():
                channels_info[channel] = len(connections)
            
            return {
                "active_connections": len(self.active_connections),
                "channels": channels_info,
                "uptime": "running" if self.heartbeat_task else "stopped",
                "connection_details": [
                    {
                        "connected_at": info["connected_at"].isoformat(),
                        "subscribed_channels": list(info["subscribed_channels"]),
                        "last_heartbeat": info["last_heartbeat"].isoformat()
                    }
                    for info in self.connection_info.values()
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de conexiones: {e}")
            return {"error": str(e)}
    
    def get_active_connections_count(self) -> int:
        """Obtener número de conexiones activas"""
        return len(self.active_connections)
    
    def get_channel_subscribers_count(self, channel: str) -> int:
        """Obtener número de suscriptores de un canal"""
        return len(self.channels.get(channel, set()))
    
    async def cleanup_stale_connections(self):
        """Limpiar conexiones inactivas"""
        try:
            current_time = datetime.utcnow()
            stale_connections = []
            
            for websocket, info in self.connection_info.items():
                last_heartbeat = info.get("last_heartbeat", current_time)
                if (current_time - last_heartbeat).total_seconds() > 300:  # 5 minutos
                    stale_connections.append(websocket)
            
            for websocket in stale_connections:
                self.logger.info("🧹 Limpiando conexión inactiva")
                self.disconnect(websocket)
                
        except Exception as e:
            self.logger.error(f"Error limpiando conexiones inactivas: {e}")
    
    async def shutdown(self):
        """Cerrar todas las conexiones"""
        try:
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            
            # Enviar mensaje de cierre a todos los clientes
            shutdown_message = {
                "type": "server_shutdown",
                "message": "Servidor cerrándose",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.broadcast(shutdown_message)
            
            # Cerrar todas las conexiones
            for websocket in self.active_connections.copy():
                try:
                    await websocket.close()
                except:
                    pass
                self.disconnect(websocket)
            
            self.logger.info("🛑 WebSocket Manager cerrado")
            
        except Exception as e:
            self.logger.error(f"Error cerrando WebSocket Manager: {e}")