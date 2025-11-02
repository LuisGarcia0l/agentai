// ============================================================================
// TIPOS PRINCIPALES DEL SISTEMA DE TRADING
// ============================================================================

export interface MarketData {
  symbol: string;
  price: number;
  change_24h: number;
  volume: number;
  timestamp: string;
}

export interface OHLCVData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TradingSignal {
  signal: 'buy' | 'sell' | 'hold';
  strength: number;
  price: number;
  timestamp: string;
  reason: string;
  indicators: Record<string, number>;
}

export interface BacktestResult {
  total_return: number;
  total_trades: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown: number;
  final_capital: number;
}

export interface BacktestRequest {
  strategy_name: string;
  parameters: Record<string, any>;
  start_date: string;
  end_date: string;
  initial_capital: number;
}

export interface AgentStatus {
  agent_id: string;
  is_running: boolean;
  last_update?: string;
  performance_metrics: Record<string, any>;
}

export interface TradingDecision {
  timestamp: string;
  symbol: string;
  action: string;
  confidence: number;
  quantity: number;
  reasoning: string;
  risk_assessment: Record<string, any>;
}

export interface Strategy {
  name: string;
  description: string;
  parameters: Record<string, StrategyParameter>;
}

export interface StrategyParameter {
  type: 'int' | 'float' | 'bool' | 'string';
  default: any;
  min?: number;
  max?: number;
  options?: string[];
}

export interface OptimizationResult {
  optimization_id: string;
  strategy_name: string;
  method: string;
  improvement_percentage: number;
  best_parameters: Record<string, any>;
  fitness_score: number;
  total_iterations: number;
  duration: string;
  recommendations: string[];
}

export interface ResearchResult {
  research_id: string;
  timestamp: string;
  total_tested: number;
  success_rate: number;
  avg_fitness: number;
  duration: string;
  best_strategies: Array<{
    name: string;
    fitness_score: number;
    risk_score: number;
    parameters: Record<string, any>;
  }>;
  recommendations: string[];
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: Record<string, boolean>;
  error?: string;
}

export interface SystemStats {
  uptime: string;
  total_requests: number;
  active_websockets: number;
  trading_decisions: number;
  research_cycles: number;
  optimizations: number;
}

export interface SystemConfig {
  trading_mode: string;
  default_symbol: string;
  max_position_size: number;
  stop_loss_percent: number;
  take_profit_percent: number;
  agent_update_interval: number;
  environment: string;
  debug: boolean;
}

// ============================================================================
// TIPOS DE UI Y ESTADO
// ============================================================================

export interface DashboardState {
  selectedSymbol: string;
  selectedTimeframe: string;
  selectedStrategy: string;
  isLiveMode: boolean;
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

export interface ChartData {
  timestamp: string;
  value: number;
  volume?: number;
  [key: string]: any;
}

export interface PortfolioPosition {
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  value: number;
}

export interface PortfolioSummary {
  total_value: number;
  total_pnl: number;
  total_pnl_percent: number;
  positions: PortfolioPosition[];
  cash_balance: number;
  exposure_percent: number;
}

// ============================================================================
// TIPOS DE WEBSOCKET
// ============================================================================

export interface WebSocketMessage {
  type: 'market_data' | 'trading_signal' | 'agent_update' | 'system_alert';
  data: any;
  timestamp: string;
}

export interface MarketDataMessage extends WebSocketMessage {
  type: 'market_data';
  data: MarketData;
}

export interface TradingSignalMessage extends WebSocketMessage {
  type: 'trading_signal';
  data: TradingSignal;
}

// ============================================================================
// TIPOS DE API
// ============================================================================

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// ============================================================================
// ENUMS
// ============================================================================

export enum SignalType {
  BUY = 'buy',
  SELL = 'sell',
  HOLD = 'hold'
}

export enum AgentType {
  TRADING = 'trading_agent',
  RESEARCH = 'research_agent',
  OPTIMIZER = 'optimizer_agent',
  RISK = 'risk_agent'
}

export enum TradingMode {
  PAPER = 'paper',
  LIVE = 'live'
}

export enum TimeFrame {
  ONE_MINUTE = '1m',
  FIVE_MINUTES = '5m',
  FIFTEEN_MINUTES = '15m',
  ONE_HOUR = '1h',
  FOUR_HOURS = '4h',
  ONE_DAY = '1d'
}

export enum StrategyType {
  RSI = 'RSI',
  MACD = 'MACD',
  BOLLINGER_BANDS = 'BollingerBands',
  MULTI_INDICATOR = 'MultiIndicator'
}