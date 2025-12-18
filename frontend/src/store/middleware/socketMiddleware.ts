/**
 * Redux middleware for Socket.IO integration.
 * Connects/disconnects socket based on auth state.
 * Dispatches actions when receiving socket events.
 */
import { Middleware } from '@reduxjs/toolkit';
import { 
  connectSocket, 
  disconnectSocket, 
  getSocket 
} from '@/services/socket';
import {
  loanUpdated,
  loanCreated,
  statusChanged,
  fetchStatistics,
} from '@/store/slices/loansSlice';
import { addNotification } from '@/store/slices/uiSlice';

// Track if listeners are set up
let listenersInitialized = false;
// Track if we've checked initial auth state
let initialAuthChecked = false;

/**
 * Setup Socket.IO event listeners.
 */
const setupSocketListeners = (dispatch: any): void => {
  const socket = getSocket();
  if (!socket || listenersInitialized) return;

  // Loan created event
  socket.on('loan_created', (data: any) => {
    console.log('[Socket.IO] Loan created:', data);
    dispatch(loanCreated(data.data));
    // Refresh statistics so dashboard counts/percentages stay in sync
    dispatch(fetchStatistics(undefined));
    dispatch(
      addNotification({
        type: 'info',
        message: `New loan created: ${data.loan_id}`,
        duration: 5000,
      })
    );
  });

  // Loan updated event
  socket.on('loan_updated', (data: any) => {
    console.log('[Socket.IO] Loan updated:', data);
    dispatch(loanUpdated({ id: data.loan_id, ...data.changes }));
    // Loan updates can affect statistics (status, risk score, etc.)
    dispatch(fetchStatistics(undefined));
  });

  // Status changed event
  socket.on('status_changed', (data: any) => {
    console.log('[Socket.IO] Status changed:', data);
    dispatch(statusChanged({
      loan_id: data.loan_id,
      old_status: data.old_status,
      new_status: data.new_status,
    }));
    dispatch(
      addNotification({
        type: data.new_status === 'APPROVED' ? 'success' : 
              data.new_status === 'REJECTED' ? 'error' : 'info',
        message: `Loan ${data.loan_id.slice(0, 8)}... status changed to ${data.new_status}`,
        duration: 5000,
      })
    );
    // Status changes directly affect by_status / by_country / totals
    dispatch(fetchStatistics(undefined));
  });

  listenersInitialized = true;
};

/**
 * Socket middleware for Redux.
 */
export const socketMiddleware: Middleware = (store) => (next) => (action: any) => {
  const result = next(action);

  // Check initial auth state on first action (when store is initialized)
  if (!initialAuthChecked) {
    initialAuthChecked = true;
    const state = store.getState() as any;
    const isAuthenticated = state?.auth?.isAuthenticated;
    const accessToken = state?.auth?.accessToken;
    
    if (isAuthenticated && accessToken) {
      console.log('[SocketMiddleware] User already authenticated, connecting socket...');
      const socket = getSocket();
      if (!socket?.connected) {
        connectSocket();
        setupSocketListeners(store.dispatch);
      }
    }
  }

  // Connect socket after successful login
  if (action.type === 'auth/login/fulfilled') {
    console.log('[SocketMiddleware] Login successful, connecting socket...');
    connectSocket();
    setupSocketListeners(store.dispatch);
  }

  // Disconnect socket on logout
  if (action.type === 'auth/logout/fulfilled' || action.type === 'auth/logout/pending') {
    console.log('[SocketMiddleware] Logout, disconnecting socket...');
    disconnectSocket();
    listenersInitialized = false;
  }

  // Reconnect socket if token was refreshed
  if (action.type === 'auth/refresh/fulfilled') {
    const socket = getSocket();
    if (!socket?.connected) {
      console.log('[SocketMiddleware] Token refreshed, reconnecting socket...');
      connectSocket();
      setupSocketListeners(store.dispatch);
    }
  }

  // Connect socket when user is fetched (after page reload)
  if (action.type === 'auth/fetchCurrentUser/fulfilled') {
    const socket = getSocket();
    if (!socket?.connected) {
      console.log('[SocketMiddleware] User fetched, connecting socket...');
      connectSocket();
      setupSocketListeners(store.dispatch);
    }
  }

  return result;
};

export default socketMiddleware;
