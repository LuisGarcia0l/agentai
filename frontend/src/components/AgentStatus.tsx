import React from 'react';
import { motion } from 'framer-motion';
import { Bot, Play, Pause, Activity, AlertCircle } from 'lucide-react';
import { useAgentsStore } from '../store';

const AgentStatus: React.FC = () => {
  const { agentsStatus } = useAgentsStore();

  const agentTypes = [
    {
      key: 'trading_agent',
      name: 'Trading Agent',
      description: 'Ejecuta operaciones',
      icon: Bot,
    },
    {
      key: 'research_agent',
      name: 'Research Agent',
      description: 'Investiga estrategias',
      icon: Activity,
    },
    {
      key: 'optimizer_agent',
      name: 'Optimizer Agent',
      description: 'Optimiza parámetros',
      icon: AlertCircle,
    },
  ];

  if (Object.keys(agentsStatus).length === 0) {
    return (
      <div className="text-center py-8">
        <Bot className="w-8 h-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Cargando estado de agentes...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {agentTypes.map((agentType, index) => {
        const agent = agentsStatus[agentType.key];
        const Icon = agentType.icon;
        
        return (
          <motion.div
            key={agentType.key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700"
          >
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Icon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                <div
                  className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${
                    agent?.is_running ? 'status-online' : 'status-offline'
                  }`}
                ></div>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                  {agentType.name}
                </h4>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {agentType.description}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className="text-right">
                <div className={`text-xs font-medium ${
                  agent?.is_running ? 'text-green-600' : 'text-red-600'
                }`}>
                  {agent?.is_running ? 'Activo' : 'Inactivo'}
                </div>
                {agent?.last_update && (
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(agent.last_update).toLocaleTimeString()}
                  </div>
                )}
              </div>
              
              <button
                className={`p-1 rounded ${
                  agent?.is_running
                    ? 'text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20'
                    : 'text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20'
                }`}
                title={agent?.is_running ? 'Detener agente' : 'Iniciar agente'}
              >
                {agent?.is_running ? (
                  <Pause className="w-4 h-4" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
              </button>
            </div>
          </motion.div>
        );
      })}
      
      {/* Resumen */}
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div className="flex items-center justify-between text-sm">
          <span className="text-blue-700 dark:text-blue-300">
            Agentes activos:
          </span>
          <span className="font-medium text-blue-900 dark:text-blue-100">
            {Object.values(agentsStatus).filter(agent => agent.is_running).length} / {Object.keys(agentsStatus).length}
          </span>
        </div>
      </div>
    </div>
  );
};

export default AgentStatus;