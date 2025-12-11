/**
 * Socket.IO client for real-time updates.
 */
import { io, Socket } from 'socket.io-client';
import { getAuthToken } from './api';

// Socket instance
let socket: Socket | null = null;

// Connection state
let isConnected = false;
let lastConnectionTime: Date | null = null;

/**
 * Get or create Socket.IO connection.
 */
export const getSocket = (): Socket | null => {
  return socket;
};

/**
 * Check if socket is connected.
 */
export const isSocketConnected = (): boolean => {
  return isConnected && socket?.connected === true;
};

/**
 * Get last connection time.
 */
export const getLastConnectionTime = (): Date | null => {
  return lastConnectionTime;
};

/**
 * Connect to Socket.IO server.
 */
export const connectSocket = (): Socket => {
  if (socket?.connected) {
    return socket;
  }

  const token = getAuthToken();

  socket = io('/loans', {
    path: '/socket.io',
    transports: ['websocket', 'polling'],
    auth: {
      token,
    },
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
  });

  socket.on('connect', () => {
    console.log('[Socket.IO] Connected:', socket?.id);
    isConnected = true;
    lastConnectionTime = new Date();
  });

  socket.on('disconnect', (reason) => {
    console.log('[Socket.IO] Disconnected:', reason);
    isConnected = false;
  });

  socket.on('connect_error', (error) => {
    console.error('[Socket.IO] Connection error:', error.message);
    isConnected = false;
  });

  return socket;
};

/**
 * Disconnect from Socket.IO server.
 */
export const disconnectSocket = (): void => {
  if (socket) {
    socket.disconnect();
    socket = null;
    isConnected = false;
  }
};

/**
 * Subscribe to country updates.
 */
export const subscribeToCountry = (countryCode: string): void => {
  if (socket?.connected) {
    socket.emit('subscribe_country', { country_code: countryCode });
  }
};

/**
 * Unsubscribe from country updates.
 */
export const unsubscribeFromCountry = (countryCode: string): void => {
  if (socket?.connected) {
    socket.emit('unsubscribe_country', { country_code: countryCode });
  }
};

/**
 * Subscribe to loan updates.
 */
export const subscribeToLoan = (loanId: string): void => {
  if (socket?.connected) {
    socket.emit('subscribe_loan', { loan_id: loanId });
  }
};

/**
 * Unsubscribe from loan updates.
 */
export const unsubscribeFromLoan = (loanId: string): void => {
  if (socket?.connected) {
    socket.emit('unsubscribe_loan', { loan_id: loanId });
  }
};

export default {
  getSocket,
  connectSocket,
  disconnectSocket,
  isSocketConnected,
  getLastConnectionTime,
  subscribeToCountry,
  unsubscribeFromCountry,
  subscribeToLoan,
  unsubscribeFromLoan,
};
