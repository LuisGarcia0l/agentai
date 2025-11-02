import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  BarChart3,
  Zap,
  AlertTriangle,
  CheckCircle,
  Clock,
  Target
} from 'lucide-react';
import { apiService, createWebSocketService } from '../services/api';
import { useMarketDataStore, useTradingSignalsStore, useAgentsStore, useDashboardStore } from '../store';
import MarketChart from '../components/MarketChart';
import TradingSignals from '../components/TradingSignals';
import AgentStatus from '../components/AgentStatus';
import PortfolioSummary from '../components/PortfolioSummary';
import toast from 'react-hot-toast';

const Dashboard: React.FC = () => {
  const [wsConnected, setWsConnected] = useState(false);
  const { selectedSymbol, currentData, setMarketData } = useMarketDataStore();
  const { addSignal } = useTradingSignalsStore();
  const { setAgentsStatus } = useAgentsStore();
  const { isLiveMode } = useDashboardStore();

  // Queries para datos iniciales
  const { data: marketTicker, isLoading: tickerLoading } = useQuery({
    queryKey: ['market-ticker', selectedSymbol],
    queryFn: () => apiService.getMarketTicker(selectedSymbol),
    refetchInterval: 5000,
  });

  const { data: agentsStatus, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents-status'],
    queryFn: () => apiService.getAgentsStatus(),
    refetchInterval: 10000,
  });

  const { data: systemHealth } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiService.getSystemHealth(),
    refetchInterval: 30000,
  });

  // WebSocket para datos en tiempo real
  useEffect(() => {
    const wsService = createWebSocketService();
    
    // Conectar a datos de mercado
    wsService.connect(
      `ws://localhost:8000/ws/market/${selectedSymbol}`,
      (data) => {
        if (data.type === 'market_data') {
          setMarketData(data.symbol, data);
        }
      },
      (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
        toast.error('Conexión WebSocket perdida');
      }
    );

    // Conectar a señales de trading
    const signalsWs = createWebSocketService();
    signalsWs.connect(
      'ws://localhost:8000/ws/signals',
      (data) => {
        if (data.type === 'trading_signal') {
          addSignal(data);
          toast.success(`Nueva señal: ${data.action.toUpperCase()}`);
        }
      }
    );

    setWsConnected(true);

    return () => {
      wsService.disconnect();
      signalsWs.disconnect();
    };
  }, [selectedSymbol, setMarketData, addSignal]);

  // Actualizar stores con datos de queries
  useEffect(() => {
    if (marketTicker) {
      setMarketData(selectedSymbol, marketTicker);
    }
  }, [marketTicker, selectedSymbol, setMarketData]);

  useEffect(() => {
    if (agentsStatus) {
      setAgentsStatus(agentsStatus);
    }
  }, [agentsStatus, setAgentsStatus]);

  const currentMarketData = currentData[selectedSymbol];
  const isPositive = currentMarketData?.change_24h && currentMarketData.change_24h > 0;

  // Métricas del dashboard
  const metrics = [
    {
      title: 'Precio Actual',
      value: currentMarketData?.price ? `$${currentMarketData.price.toLocaleString()}` : '--',
      change: currentMarketData?.change_24h ? `${currentMarketData.change_24h.toFixed(2)}%` : '--',
      icon: DollarSign,
      color: isPositive ? 'text-green-600' : 'text-red-600',
      bgColor: isPositive ? 'bg-green-50' : 'bg-red-50',
      borderColor: isPositive ? 'border-green-200' : 'border-red-200',
    },
    {
      title: 'Volumen 24h',
      value: currentMarketData?.volume ? `${(currentMarketData.volume / 1000000).toFixed(1)}M` : '--',
      change: '+12.5%',
      icon: BarChart3,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
    },
    {
      title: 'Agentes Activos',
      value: agentsStatus ? Object.values(agentsStatus).filter(agent => agent.is_running).length.toString() : '--',
      change: `${agentsStatus ? Object.keys(agentsStatus).length : 0} total`,
      icon: Activity,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
    },
    {
      title: 'Estado Sistema',
      value: systemHealth?.status === 'healthy' ? 'Saludable' : 'Degradado',
      change: wsConnected ? 'Conectado' : 'Desconectado',
      icon: systemHealth?.status === 'healthy' ? CheckCircle : AlertTriangle,
      color: systemHealth?.status === 'healthy' ? 'text-green-600' : 'text-yellow-600',
      bgColor: systemHealth?.status === 'healthy' ? 'bg-green-50' : 'bg-yellow-50',
      borderColor: systemHealth?.status === 'healthy' ? 'border-green-200' : 'border-yellow-200',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header con métricas principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => {
          const Icon = metric.icon;
          return (
            <motion.div
              key={metric.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`${metric.bgColor} ${metric.borderColor} border rounded-xl p-6 card-hover`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {metric.title}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                    {metric.value}
                  </p>
                  <p className={`text-sm ${metric.color} mt-1`}>
                    {metric.change}
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${metric.bgColor}`}>
                  <Icon className={`w-6 h-6 ${metric.color}`} />
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Contenido principal */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Gráfico de precios */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Gráfico de Precios
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {selectedSymbol} - Tiempo real
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {wsConnected ? 'En vivo' : 'Desconectado'}
                </span>
              </div>
            </div>
            <MarketChart symbol={selectedSymbol} />
          </div>
        </motion.div>

        {/* Panel lateral */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-6"
        >
          {/* Señales de trading */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Señales de Trading
              </h3>
              <Target className="w-5 h-5 text-blue-500" />
            </div>
            <TradingSignals />
          </div>

          {/* Estado de agentes */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Agentes IA
              </h3>
              <Zap className="w-5 h-5 text-purple-500" />
            </div>
            <AgentStatus />
          </div>
        </motion.div>
      </div>

      {/* Resumen del portafolio */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Resumen del Portafolio
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Estado actual de posiciones y rendimiento
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-gray-400" />
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Actualizado hace 2 min
              </span>
            </div>
          </div>
          <PortfolioSummary />
        </div>
      </motion.div>

      {/* Alertas y notificaciones */}
      {!isLiveMode && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4"
        >
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <div>
              <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100">
                Modo Paper Trading Activo
              </h4>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Todas las operaciones son simuladas. No se ejecutarán trades reales.
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default Dashboard;