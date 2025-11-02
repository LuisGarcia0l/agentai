import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService } from '../services/api';
import { useMarketDataStore } from '../store';

interface MarketChartProps {
  symbol: string;
}

const MarketChart: React.FC<MarketChartProps> = ({ symbol }) => {
  const { selectedTimeframe } = useMarketDataStore();

  const { data: ohlcvData, isLoading, error } = useQuery({
    queryKey: ['ohlcv', symbol, selectedTimeframe],
    queryFn: () => apiService.getOHLCVData(symbol, selectedTimeframe, 100),
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="spinner w-8 h-8"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-64 flex items-center justify-center">
        <p className="text-red-500">Error cargando datos del gráfico</p>
      </div>
    );
  }

  const chartData = ohlcvData?.data.map(candle => ({
    timestamp: new Date(candle.timestamp).toLocaleTimeString(),
    price: candle.close,
    volume: candle.volume,
  })) || [];

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis 
            dataKey="timestamp" 
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            domain={['dataMin - 100', 'dataMax + 100']}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              border: 'none',
              borderRadius: '8px',
              color: 'white'
            }}
            formatter={(value: number) => [`$${value.toLocaleString()}`, 'Precio']}
          />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#3b82f6' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MarketChart;