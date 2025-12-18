/**
 * Real-time connection indicator component.
 */
import { useState, useEffect } from 'react';
import { isSocketConnected } from '@/services/socket';
import clsx from 'clsx';

const RealTimeIndicator = () => {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Check connection status periodically
    const checkConnection = () => {
      setConnected(isSocketConnected());
    };

    checkConnection();
    const interval = setInterval(checkConnection, 2000);

    return () => clearInterval(interval);
  }, []);

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
    </div>
  );
};

export default RealTimeIndicator;
