/**
 * Real-time connection indicator component.
 */
import { useState, useEffect } from 'react';
import { isSocketConnected, getLastConnectionTime } from '@/services/socket';
import clsx from 'clsx';

const RealTimeIndicator = () => {
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    // Check connection status periodically
    const checkConnection = () => {
      setConnected(isSocketConnected());
      setLastUpdate(getLastConnectionTime());
    };

    checkConnection();
    const interval = setInterval(checkConnection, 2000);

    return () => clearInterval(interval);
  }, []);

  const formatTime = (date: Date | null) => {
    if (!date) return 'Never';
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex items-center gap-2 text-sm">
      <div className="flex items-center gap-1.5">
        <div
          className={clsx(
            'w-2 h-2 rounded-full',
            connected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
          )}
        />
        <span className={connected ? 'text-green-600' : 'text-gray-500'}>
          {connected ? 'Live' : 'Offline'}
        </span>
      </div>
      {connected && lastUpdate && (
        <span className="text-gray-400 text-xs">
          Connected at {formatTime(lastUpdate)}
        </span>
      )}
    </div>
  );
};

export default RealTimeIndicator;
