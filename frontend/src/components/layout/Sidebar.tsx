/**
 * Sidebar navigation component.
 */
import { NavLink, useNavigate } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { setFilters, fetchLoans } from '@/store/slices/loansSlice';
import clsx from 'clsx';
import type { LoanStatus, CountryCode } from '@/types/loan';

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
}

const navigation: NavItem[] = [
  {
    name: 'Dashboard',
    path: '/dashboard',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
        />
      </svg>
    ),
  },
  {
    name: 'All Loans',
    path: '/loans',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
        />
      </svg>
    ),
  },
  {
    name: 'Create Loan',
    path: '/loans/new',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 6v6m0 0v6m0-6h6m-6 0H6"
        />
      </svg>
    ),
  },
];

const countries = [
  { code: 'ES', name: 'España', flag: '🇪🇸' },
  { code: 'MX', name: 'México', flag: '🇲🇽' },
  { code: 'CO', name: 'Colombia', flag: '🇨🇴' },
  { code: 'BR', name: 'Brasil', flag: '🇧🇷' },
];

const statuses: { value: LoanStatus; label: string; color: string; dotColor: string }[] = [
  { value: 'PENDING', label: 'Pending', color: 'bg-yellow-100 text-yellow-800', dotColor: 'bg-yellow-500' },
  { value: 'VALIDATING', label: 'Validating', color: 'bg-blue-100 text-blue-800', dotColor: 'bg-blue-400' },
  { value: 'IN_REVIEW', label: 'In Review', color: 'bg-purple-100 text-purple-800', dotColor: 'bg-purple-500' },
  { value: 'APPROVED', label: 'Approved', color: 'bg-green-100 text-green-800', dotColor: 'bg-green-500' },
  { value: 'REJECTED', label: 'Rejected', color: 'bg-red-100 text-red-800', dotColor: 'bg-red-500' },
  { value: 'CANCELLED', label: 'Cancelled', color: 'bg-gray-100 text-gray-800', dotColor: 'bg-gray-400' },
  { value: 'DISBURSED', label: 'Disbursed', color: 'bg-teal-100 text-teal-800', dotColor: 'bg-teal-500' },
  { value: 'COMPLETED', label: 'Completed', color: 'bg-emerald-100 text-emerald-800', dotColor: 'bg-emerald-600' },
];

const Sidebar = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { sidebarOpen } = useAppSelector((state) => state.ui);
  const { filters } = useAppSelector((state) => state.loans);
  const { user } = useAppSelector((state) => state.auth);
  
  const canCreateLoan = user?.role === 'ADMIN' || user?.role === 'ANALYST';

  const handleCountryFilter = (code: CountryCode) => {
    const newCountryCode = filters.country_code === code ? null : code;
    dispatch(setFilters({ 
      country_code: newCountryCode,
      page: 1 
    }));
    // Navigate to loans page and fetch with filter
    navigate('/loans');
    dispatch(fetchLoans({ 
      country_code: newCountryCode || undefined,
      page: 1 
    }));
  };

  const handleStatusFilter = (status: LoanStatus) => {
    const newStatus = filters.status === status ? null : status;
    dispatch(setFilters({ 
      status: newStatus,
      page: 1 
    }));
    // Navigate to loans page and fetch with filter
    navigate('/loans');
    dispatch(fetchLoans({ 
      status: newStatus || undefined,
      page: 1 
    }));
  };

  if (!sidebarOpen) return null;

  return (
    <aside className="fixed left-0 top-16 w-64 h-[calc(100vh-4rem)] bg-white border-r border-gray-200 overflow-y-auto z-20">
      <div className="p-4">
        {/* Main navigation */}
        <nav className="space-y-1">
          {navigation
            .filter((item) => item.path !== '/loans/new' || canCreateLoan)
            .map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  )
                }
              >
                {item.icon}
                {item.name}
              </NavLink>
            ))}
        </nav>

        {/* Divider */}
        <hr className="my-4 border-gray-200" />

        {/* Country filters */}
        <div className="mb-4">
          <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Filter by Country
          </h3>
          <div className="space-y-1">
            {countries.map((country) => (
              <button
                key={country.code}
                onClick={() => handleCountryFilter(country.code as CountryCode)}
                className={clsx(
                  'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                  filters.country_code === country.code
                    ? 'bg-primary-50 text-primary-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                )}
              >
                <span className="text-lg">{country.flag}</span>
                {country.name}
              </button>
            ))}
          </div>
        </div>

        {/* Status filters */}
        <div>
          <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Filter by Status
          </h3>
          <div className="space-y-1">
            {statuses.map((status) => (
              <button
                key={status.value}
                onClick={() => handleStatusFilter(status.value)}
                className={clsx(
                  'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                  filters.status === status.value
                    ? 'bg-primary-50 font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                )}
              >
                <span
                  className={clsx('w-2 h-2 rounded-full', status.dotColor)}
                />
                {status.label}
              </button>
            ))}
          </div>
        </div>

        {/* Clear filters */}
        {(filters.country_code || filters.status) && (
          <button
            onClick={() => dispatch(setFilters({ country_code: null, status: null, page: 1 }))}
            className="w-full mt-4 px-3 py-2 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg"
          >
            Clear all filters
          </button>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
