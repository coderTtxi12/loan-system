/**
 * Main layout wrapper component.
 */
import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchCurrentUser } from '@/store/slices/authSlice';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import clsx from 'clsx';

const Layout = () => {
  const dispatch = useAppDispatch();
  const { sidebarOpen } = useAppSelector((state) => state.ui);
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);

  // Fetch current user if authenticated but user data is missing
  useEffect(() => {
    if (isAuthenticated && !user) {
      dispatch(fetchCurrentUser());
    }
  }, [dispatch, isAuthenticated, user]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top navbar */}
      <Navbar />

      {/* Sidebar */}
      <Sidebar />

      {/* Main content area */}
      <main
        className={clsx(
          'pt-16 min-h-screen transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-0'
        )}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
