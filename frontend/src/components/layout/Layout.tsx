/**
 * Main layout wrapper component.
 */
import { Outlet } from 'react-router-dom';
import { useAppSelector } from '@/store/hooks';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import clsx from 'clsx';

const Layout = () => {
  const { sidebarOpen } = useAppSelector((state) => state.ui);

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
