import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  MarketData,
  TradingSignal,
  AgentStatus,
  TradingDecision,
  SystemHealth,
  SystemConfig,
  Notification,
  DashboardState,
  PortfolioSummary
} from '../types';

// ============================================================================
// MARKET DATA STORE
// ============================================================================

interface MarketDataState {
  currentData: Record<string, MarketData>;
  selectedSymbol: string;
  selectedTimeframe: string;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setMarketData: (symbol: string, data: MarketData) => void;
  setSelectedSymbol: (symbol: string) => void;
  setSelectedTimeframe: (timeframe: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useMarketDataStore = create<MarketDataState>()(
  devtools(
    (set) => ({
      currentData: {},
      selectedSymbol: 'BTCUSDT',
      selectedTimeframe: '1h',
      isLoading: false,
      error: null,

      setMarketData: (symbol, data) =>
        set((state) => ({
          currentData: { ...state.currentData, [symbol]: data }
        })),

      setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
      setSelectedTimeframe: (timeframe) => set({ selectedTimeframe: timeframe }),
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
    }),
    { name: 'market-data-store' }
  )
);

// ============================================================================
// TRADING SIGNALS STORE
// ============================================================================

interface TradingSignalsState {
  signals: TradingSignal[];
  latestSignal: TradingSignal | null;
  isLoading: boolean;
  
  // Actions
  addSignal: (signal: TradingSignal) => void;
  setLatestSignal: (signal: TradingSignal) => void;
  clearSignals: () => void;
  setLoading: (loading: boolean) => void;
}

export const useTradingSignalsStore = create<TradingSignalsState>()(
  devtools(
    (set) => ({
      signals: [],
      latestSignal: null,
      isLoading: false,

      addSignal: (signal) =>
        set((state) => ({
          signals: [signal, ...state.signals].slice(0, 100), // Keep last 100 signals
          latestSignal: signal
        })),

      setLatestSignal: (signal) => set({ latestSignal: signal }),
      clearSignals: () => set({ signals: [], latestSignal: null }),
      setLoading: (loading) => set({ isLoading: loading }),
    }),
    { name: 'trading-signals-store' }
  )
);

// ============================================================================
// AGENTS STORE
// ============================================================================

interface AgentsState {
  agentsStatus: Record<string, AgentStatus>;
  tradingDecisions: TradingDecision[];
  isLoading: boolean;
  
  // Actions
  setAgentsStatus: (status: Record<string, AgentStatus>) => void;
  updateAgentStatus: (agentId: string, status: AgentStatus) => void;
  setTradingDecisions: (decisions: TradingDecision[]) => void;
  addTradingDecision: (decision: TradingDecision) => void;
  setLoading: (loading: boolean) => void;
}

export const useAgentsStore = create<AgentsState>()(
  devtools(
    (set) => ({
      agentsStatus: {},
      tradingDecisions: [],
      isLoading: false,

      setAgentsStatus: (status) => set({ agentsStatus: status }),
      
      updateAgentStatus: (agentId, status) =>
        set((state) => ({
          agentsStatus: { ...state.agentsStatus, [agentId]: status }
        })),

      setTradingDecisions: (decisions) => set({ tradingDecisions: decisions }),
      
      addTradingDecision: (decision) =>
        set((state) => ({
          tradingDecisions: [decision, ...state.tradingDecisions].slice(0, 50)
        })),

      setLoading: (loading) => set({ isLoading: loading }),
    }),
    { name: 'agents-store' }
  )
);

// ============================================================================
// DASHBOARD STORE
// ============================================================================

interface DashboardStoreState extends DashboardState {
  // Actions
  setSelectedSymbol: (symbol: string) => void;
  setSelectedTimeframe: (timeframe: string) => void;
  setSelectedStrategy: (strategy: string) => void;
  setLiveMode: (isLive: boolean) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
}

export const useDashboardStore = create<DashboardStoreState>()(
  devtools(
    persist(
      (set) => ({
        selectedSymbol: 'BTCUSDT',
        selectedTimeframe: '1h',
        selectedStrategy: 'RSI',
        isLiveMode: false,
        notifications: [],

        setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
        setSelectedTimeframe: (timeframe) => set({ selectedTimeframe: timeframe }),
        setSelectedStrategy: (strategy) => set({ selectedStrategy: strategy }),
        setLiveMode: (isLive) => set({ isLiveMode: isLive }),
        
        addNotification: (notification) =>
          set((state) => ({
            notifications: [
              {
                ...notification,
                id: Date.now().toString(),
                timestamp: new Date(),
                read: false,
              },
              ...state.notifications,
            ].slice(0, 20),
          })),
      }),
      {
        name: 'dashboard-store',
        partialize: (state) => ({
          selectedSymbol: state.selectedSymbol,
          selectedTimeframe: state.selectedTimeframe,
          selectedStrategy: state.selectedStrategy,
          isLiveMode: state.isLiveMode,
        }),
      }
    ),
    { name: 'dashboard-store' }
  )
);