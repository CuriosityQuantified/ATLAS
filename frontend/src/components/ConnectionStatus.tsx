'use client'

interface ConnectionStatusProps {
  status: 'disconnected' | 'connecting' | 'connected';
  taskStatus?: string;
}

export default function ConnectionStatus({ status, taskStatus }: ConnectionStatusProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'bg-green-500/20 text-green-400';
      case 'connecting':
        return 'bg-yellow-500/20 text-yellow-400';
      default:
        return 'bg-gray-500/20 text-gray-400';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'connected':
        return '🟢';
      case 'connecting':
        return '🟡';
      default:
        return '⚪';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      default:
        return 'Disconnected';
    }
  };

  return (
    <div className="flex items-center space-x-2">
      {taskStatus && (
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
          taskStatus === 'active' ? 'bg-green-500/20 text-green-400' :
          taskStatus === 'completed' ? 'bg-blue-500/20 text-blue-400' :
          'bg-red-500/20 text-red-400'
        }`}>
          {taskStatus}
        </span>
      )}
      
      <span className={`px-3 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${getStatusColor()}`}>
        <span>{getStatusIcon()}</span>
        <span>{getStatusText()}</span>
      </span>
    </div>
  );
}