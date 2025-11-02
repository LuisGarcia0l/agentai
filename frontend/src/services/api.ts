import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  MarketData,
  OHLCVData,
  TradingSignal,
  BacktestResult,
  BacktestRequest,
  AgentStatus,
  TradingDecision,
  Strategy,
  OptimizationResult,
  ResearchResult,
  SystemHealth,
  SystemStats,
  SystemConfig,
  ApiResponse
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor para manejo de errores
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // ============================================================================
  // MARKET DATA ENDPOINTS
  // ============================================================================

  async getMarketTicker(symbol: string): Promise<MarketData> {
    const response: AxiosResponse<MarketData> = await this.api.get(`/market/ticker/${symbol}`);
    return response.data;
  }

  async getOHLCVData(
    symbol: string,
    timeframe: string = '1h',
    limit: number = 100
  ): Promise<{ symbol: string; timeframe: string; data: OHLCVData[] }> {
    const response = await this.api.get(`/market/ohlcv/${symbol}`, {
      params: { timeframe, limit }
    });
    return response.data;
  }

  async getAvailableSymbols(): Promise<{ symbols: string[] }> {
    const response = await this.api.get('/market/symbols');
    return response.data;
  }

  // ============================================================================
  // AGENTS ENDPOINTS
  // ============================================================================

  async getAgentsStatus(): Promise<Record<string, AgentStatus>> {
    const response = await this.api.get('/agents/status');
    return response.data;
  }

  async startTradingAgent(): Promise<{ message: string; status: string }> {
    const response = await this.api.post('/agents/trading/start');
    return response.data;
  }

  async stopTradingAgent(): Promise<{ message: string; status: string }> {
    const response = await this.api.post('/agents/trading/stop');
    return response.data;
  }

  async getTradingDecisions(limit: number = 50): Promise<{ decisions: TradingDecision[] }> {
    const response = await this.api.get('/agents/trading/decisions', {
      params: { limit }
    });
    return response.data;
  }

  // ============================================================================
  // STRATEGIES ENDPOINTS
  // ============================================================================

  async getAvailableStrategies(): Promise<{ strategies: Strategy[] }> {
    const response = await this.api.get('/strategies/available');
    return response.data;
  }

  async getTradingSignal(
    strategyName: string,
    symbol: string = 'BTCUSDT',
    parameters?: Record<string, any>
  ): Promise<TradingSignal> {
    const response = await this.api.post('/strategies/signal', {
      strategy_name: strategyName,
      symbol,
      parameters
    });
    return response.data;
  }

  // ============================================================================
  // BACKTESTING ENDPOINTS
  // ============================================================================

  async runBacktest(request: BacktestRequest): Promise<BacktestResult> {
    const response = await this.api.post('/backtest/run', request);
    return response.data;
  }

  // ============================================================================
  // OPTIMIZATION ENDPOINTS
  // ============================================================================

  async runOptimization(
    strategyName: string,
    baseParameters: Record<string, any>,
    optimizationMethod: string = 'genetic_algorithm'
  ): Promise<OptimizationResult> {
    const response = await this.api.post('/optimization/run', {
      strategy_name: strategyName,
      base_parameters: baseParameters,
      optimization_method: optimizationMethod
    });
    return response.data;
  }

  // ============================================================================
  // RESEARCH ENDPOINTS
  // ============================================================================

  async runResearch(): Promise<ResearchResult> {
    const response = await this.api.post('/research/run');
    return response.data;
  }

  // ============================================================================
  // SYSTEM ENDPOINTS
  // ============================================================================

  async getSystemHealth(): Promise<SystemHealth> {
    const response = await this.api.get('/health');
    return response.data;
  }

  async getSystemStats(): Promise<SystemStats> {
    const response = await this.api.get('/stats');
    return response.data;
  }

  async getSystemConfig(): Promise<SystemConfig> {
    const response = await this.api.get('/config');
    return response.data;
  }

  async updateSystemConfig(updates: Partial<SystemConfig>): Promise<{ message: string; updated_fields: string[] }> {
    const response = await this.api.post('/config/update', updates);
    return response.data;
  }
}

// ============================================================================
// WEBSOCKET SERVICE
// ============================================================================

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 5000;

  connect(url: string, onMessage: (data: any) => void, onError?: (error: Event) => void) {
    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('WebSocket connected:', url);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect(url, onMessage, onError);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (onError) onError(error);
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      if (onError) onError(error as Event);
    }
  }

  private attemptReconnect(url: string, onMessage: (data: any) => void, onError?: (error: Event) => void) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect(url, onMessage, onError);
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Instancia singleton del servicio API
export const apiService = new ApiService();

// Factory para crear instancias de WebSocket
export const createWebSocketService = () => new WebSocketService();