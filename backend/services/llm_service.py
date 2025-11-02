"""
Servicio para interactuar con modelos de lenguaje (LLM)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import json

from backend.core.config import settings

class LLMService:
    """
    Servicio para interactuar con modelos de lenguaje
    
    Soporta:
    - OpenAI GPT
    - Anthropic Claude
    - Modo simulación para desarrollo
    """
    
    def __init__(self):
        self.logger = logging.getLogger("services.llm")
        self.config = settings.get_llm_config()
        self.client = None
        self.is_initialized = False
        
    async def initialize(self):
        """Inicializar el servicio LLM"""
        try:
            if self.config["provider"] == "openai":
                await self._initialize_openai()
            elif self.config["provider"] == "anthropic":
                await self._initialize_anthropic()
            else:
                # Modo simulación
                self.logger.info("🤖 LLM Service en modo simulación")
                self.is_initialized = True
                
        except Exception as e:
            self.logger.error(f"Error inicializando LLM service: {e}")
            self.logger.info("🤖 Fallback a modo simulación")
            self.config["provider"] = "mock"
            self.is_initialized = True
    
    async def _initialize_openai(self):
        """Inicializar cliente OpenAI"""
        try:
            import openai
            
            openai.api_key = self.config["api_key"]
            self.client = openai
            
            # Verificar conectividad
            response = await self._make_openai_request(
                "Responde solo 'OK' si puedes procesar este mensaje.",
                max_tokens=10
            )
            
            if response:
                self.logger.info("✅ Conectado a OpenAI")
                self.is_initialized = True
            else:
                raise Exception("No se pudo verificar conexión con OpenAI")
                
        except ImportError:
            self.logger.error("Librería openai no instalada")
            raise
        except Exception as e:
            self.logger.error(f"Error inicializando OpenAI: {e}")
            raise
    
    async def _initialize_anthropic(self):
        """Inicializar cliente Anthropic"""
        try:
            import anthropic
            
            self.client = anthropic.Anthropic(api_key=self.config["api_key"])
            
            # Verificar conectividad
            response = await self._make_anthropic_request(
                "Responde solo 'OK' si puedes procesar este mensaje.",
                max_tokens=10
            )
            
            if response:
                self.logger.info("✅ Conectado a Anthropic Claude")
                self.is_initialized = True
            else:
                raise Exception("No se pudo verificar conexión con Anthropic")
                
        except ImportError:
            self.logger.error("Librería anthropic no instalada")
            raise
        except Exception as e:
            self.logger.error(f"Error inicializando Anthropic: {e}")
            raise
    
    async def _make_openai_request(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> Optional[str]:
        """Hacer request a OpenAI"""
        try:
            response = await self.client.ChatCompletion.acreate(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": "Eres un asistente especializado en análisis financiero y trading."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error en request OpenAI: {e}")
            return None
    
    async def _make_anthropic_request(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> Optional[str]:
        """Hacer request a Anthropic"""
        try:
            response = await self.client.messages.create(
                model=self.config["model"],
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            self.logger.error(f"Error en request Anthropic: {e}")
            return None
    
    async def _make_mock_request(self, prompt: str, analysis_type: str = "general") -> str:
        """Generar respuesta simulada para desarrollo"""
        
        if "análisis técnico" in prompt.lower() or "technical analysis" in prompt.lower():
            return """
            Análisis Técnico:
            
            Basado en los indicadores proporcionados, el activo muestra:
            
            • RSI: Indica condiciones de sobrecompra/sobreventa según el valor actual
            • MACD: La divergencia sugiere un posible cambio de tendencia
            • Medias Móviles: La configuración actual sugiere una tendencia alcista/bajista
            • Volumen: El volumen de trading está por encima/debajo del promedio
            
            Recomendación: Considerar entrada/salida basada en la confluencia de señales.
            Gestión de riesgo: Implementar stop-loss apropiado según volatilidad.
            """
        
        elif "sentimiento" in prompt.lower() or "sentiment" in prompt.lower():
            return """
            Análisis de Sentimiento: NEUTRAL
            
            El mercado muestra señales mixtas:
            • Indicadores técnicos en rango neutral
            • Volumen moderado sugiere consolidación
            • Sin señales claras de ruptura direccional
            
            Recomendación: Esperar confirmación antes de tomar posiciones significativas.
            """
        
        elif "mercado" in prompt.lower() or "market" in prompt.lower():
            return """
            Análisis de Mercado:
            
            Condiciones actuales del mercado:
            • Volatilidad: Moderada
            • Tendencia: Lateral con sesgo alcista/bajista
            • Oportunidades: Identificadas en activos con momentum
            
            Factores a considerar:
            • Correlaciones entre activos principales
            • Niveles de soporte y resistencia clave
            • Gestión de riesgo apropiada para el entorno actual
            """
        
        else:
            return """
            Análisis Financiero:
            
            Basado en los datos proporcionados, se observa:
            • Tendencia general del activo
            • Niveles de riesgo actuales
            • Oportunidades potenciales
            
            Recomendación: Mantener enfoque disciplinado en gestión de riesgo
            y seguimiento de indicadores clave.
            """
    
    async def analyze_market_data(self, context: str) -> str:
        """Analizar datos de mercado usando LLM"""
        try:
            prompt = f"""
            Como experto en análisis técnico y trading, analiza los siguientes datos de mercado:
            
            {context}
            
            Proporciona un análisis conciso que incluya:
            1. Interpretación de los indicadores técnicos
            2. Evaluación de la tendencia actual
            3. Identificación de niveles clave de soporte/resistencia
            4. Recomendación de trading (compra/venta/esperar)
            5. Gestión de riesgo sugerida
            
            Mantén el análisis profesional y basado en datos.
            """
            
            if self.config["provider"] == "openai":
                return await self._make_openai_request(prompt)
            elif self.config["provider"] == "anthropic":
                return await self._make_anthropic_request(prompt)
            else:
                return await self._make_mock_request(prompt, "technical")
                
        except Exception as e:
            self.logger.error(f"Error analizando datos de mercado: {e}")
            return "Error en análisis: No se pudo procesar la información de mercado."
    
    async def analyze_sentiment(self, context: str) -> str:
        """Analizar sentimiento del mercado"""
        try:
            prompt = f"""
            Como analista de sentimiento de mercado, evalúa el siguiente contexto:
            
            {context}
            
            Proporciona un análisis de sentimiento que incluya:
            1. Sentimiento general (Bullish/Bearish/Neutral)
            2. Factores que influyen en el sentimiento
            3. Nivel de confianza en el análisis
            4. Posibles catalizadores que podrían cambiar el sentimiento
            
            Sé específico y justifica tu evaluación.
            """
            
            if self.config["provider"] == "openai":
                return await self._make_openai_request(prompt)
            elif self.config["provider"] == "anthropic":
                return await self._make_anthropic_request(prompt)
            else:
                return await self._make_mock_request(prompt, "sentiment")
                
        except Exception as e:
            self.logger.error(f"Error analizando sentimiento: {e}")
            return "Error en análisis: No se pudo evaluar el sentimiento del mercado."
    
    async def generate_trading_strategy(self, parameters: Dict[str, Any]) -> str:
        """Generar estrategia de trading usando LLM"""
        try:
            prompt = f"""
            Como estratega de trading cuantitativo, diseña una estrategia basada en:
            
            Parámetros:
            {json.dumps(parameters, indent=2)}
            
            Genera una estrategia que incluya:
            1. Lógica de entrada y salida
            2. Indicadores técnicos a utilizar
            3. Gestión de riesgo (stop-loss, take-profit)
            4. Condiciones de mercado óptimas
            5. Parámetros recomendados
            
            Proporciona una estrategia práctica y implementable.
            """
            
            if self.config["provider"] == "openai":
                return await self._make_openai_request(prompt, max_tokens=800)
            elif self.config["provider"] == "anthropic":
                return await self._make_anthropic_request(prompt, max_tokens=800)
            else:
                return await self._make_mock_request(prompt, "strategy")
                
        except Exception as e:
            self.logger.error(f"Error generando estrategia: {e}")
            return "Error: No se pudo generar la estrategia de trading."
    
    async def optimize_parameters(self, strategy_results: List[Dict[str, Any]]) -> str:
        """Optimizar parámetros basado en resultados"""
        try:
            prompt = f"""
            Como optimizador de estrategias de trading, analiza los siguientes resultados:
            
            Resultados de backtesting:
            {json.dumps(strategy_results[:5], indent=2)}  # Limitar para no exceder tokens
            
            Proporciona recomendaciones para:
            1. Parámetros que necesitan ajuste
            2. Rangos óptimos sugeridos
            3. Trade-offs identificados
            4. Métricas a priorizar
            5. Próximos pasos de optimización
            
            Enfócate en mejoras prácticas y medibles.
            """
            
            if self.config["provider"] == "openai":
                return await self._make_openai_request(prompt, max_tokens=600)
            elif self.config["provider"] == "anthropic":
                return await self._make_anthropic_request(prompt, max_tokens=600)
            else:
                return await self._make_mock_request(prompt, "optimization")
                
        except Exception as e:
            self.logger.error(f"Error optimizando parámetros: {e}")
            return "Error: No se pudo generar recomendaciones de optimización."
    
    async def generate_risk_assessment(self, portfolio_data: Dict[str, Any]) -> str:
        """Generar evaluación de riesgo"""
        try:
            prompt = f"""
            Como gestor de riesgo, evalúa el siguiente portafolio:
            
            Datos del portafolio:
            {json.dumps(portfolio_data, indent=2)}
            
            Proporciona una evaluación que incluya:
            1. Nivel de riesgo general (Bajo/Medio/Alto/Crítico)
            2. Principales fuentes de riesgo identificadas
            3. Métricas de riesgo clave
            4. Recomendaciones de mitigación
            5. Límites de riesgo sugeridos
            
            Sé específico en las recomendaciones de acción.
            """
            
            if self.config["provider"] == "openai":
                return await self._make_openai_request(prompt, max_tokens=600)
            elif self.config["provider"] == "anthropic":
                return await self._make_anthropic_request(prompt, max_tokens=600)
            else:
                return await self._make_mock_request(prompt, "risk")
                
        except Exception as e:
            self.logger.error(f"Error evaluando riesgo: {e}")
            return "Error: No se pudo generar la evaluación de riesgo."
    
    async def generate_market_report(self, market_data: Dict[str, Any]) -> str:
        """Generar reporte de mercado"""
        try:
            prompt = f"""
            Como analista de mercado, genera un reporte basado en:
            
            Datos de mercado:
            {json.dumps(market_data, indent=2)}
            
            El reporte debe incluir:
            1. Resumen ejecutivo del estado del mercado
            2. Análisis de tendencias principales
            3. Oportunidades identificadas
            4. Riesgos a considerar
            5. Outlook de corto y mediano plazo
            
            Mantén un tono profesional y objetivo.
            """
            
            if self.config["provider"] == "openai":
                return await self._make_openai_request(prompt, max_tokens=800)
            elif self.config["provider"] == "anthropic":
                return await self._make_anthropic_request(prompt, max_tokens=800)
            else:
                return await self._make_mock_request(prompt, "market")
                
        except Exception as e:
            self.logger.error(f"Error generando reporte: {e}")
            return "Error: No se pudo generar el reporte de mercado."
    
    async def explain_strategy_performance(self, performance_data: Dict[str, Any]) -> str:
        """Explicar performance de estrategia"""
        try:
            prompt = f"""
            Como analista de performance, explica los siguientes resultados:
            
            Datos de performance:
            {json.dumps(performance_data, indent=2)}
            
            Proporciona una explicación que incluya:
            1. Análisis de los resultados principales
            2. Fortalezas y debilidades identificadas
            3. Factores que contribuyeron al performance
            4. Comparación con benchmarks típicos
            5. Recomendaciones de mejora
            
            Usa un lenguaje claro y educativo.
            """
            
            if self.config["provider"] == "openai":
                return await self._make_openai_request(prompt, max_tokens=700)
            elif self.config["provider"] == "anthropic":
                return await self._make_anthropic_request(prompt, max_tokens=700)
            else:
                return await self._make_mock_request(prompt, "performance")
                
        except Exception as e:
            self.logger.error(f"Error explicando performance: {e}")
            return "Error: No se pudo generar la explicación de performance."