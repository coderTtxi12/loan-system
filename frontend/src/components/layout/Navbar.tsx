/**
 * Top navigation bar component.
 */
import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { logout } from '@/store/slices/authSlice';
import { toggleSidebar } from '@/store/slices/uiSlice';

const Navbar = () => {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  const { sidebarOpen } = useAppSelector((state) => state.ui);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleLogout = () => {
    dispatch(logout());
    setDropdownOpen(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };

    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownOpen]);

  return (
    <nav className="bg-white border-b border-gray-200 fixed w-full z-30 top-0">
      <div className="px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Left side - Logo and hamburger */}
          <div className="flex items-center">
            {/* Hamburger menu */}
            <button
              onClick={() => dispatch(toggleSidebar())}
              className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200"
              aria-label="Toggle sidebar"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {sidebarOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                )}
              </svg>
            </button>

            {/* Logo */}
            <Link to="/dashboard" className="flex items-center ml-4">
              <span className="text-2xl mr-2">🏦</span>
              <span className="text-xl font-bold text-primary-600">
                Loan System
              </span>
            </Link>
          </div>

          {/* Right side - User menu */}
          <div className="flex items-center gap-4">
            {/* Country flags */}
            <div className="hidden md:flex items-center gap-2 text-lg">
              <span title="España">🇪🇸</span>
              <span title="México">🇲🇽</span>
              <span title="Colombia">🇨🇴</span>
              <span title="Brasil">🇧🇷</span>
            </div>

            {/* User info */}
            {user && (
              <div className="flex items-center gap-3">
                <div className="hidden md:block text-right">
                  <p className="text-sm font-medium text-gray-700">
                    {user.full_name}
                  </p>
                  <p className="text-xs text-gray-500">{user.role}</p>
                </div>

                {/* User avatar */}
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setDropdownOpen(!dropdownOpen)}
                    className="w-10 h-10 rounded-full bg-primary-100 text-primary-600 font-semibold flex items-center justify-center hover:bg-primary-200 transition-colors"
                  >
                    {user.full_name.charAt(0).toUpperCase()}
                  </button>

                  {/* Dropdown menu */}
                  {dropdownOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-50">
                      <div className="px-4 py-2 border-b">
                        <p className="text-sm font-medium text-gray-900">
                          {user.full_name}
                        </p>
                        <p className="text-xs text-gray-500">{user.email}</p>
                      </div>
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
