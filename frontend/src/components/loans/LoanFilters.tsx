/**
 * Loan filters component.
 */
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setFilters, clearFilters, fetchLoans } from '@/store/slices/loansSlice';
import { Button } from '@/components/ui';
import type { CountryCode, LoanStatus } from '@/types/loan';

const countries: { code: CountryCode; name: string; flag: string }[] = [
  { code: 'ES', name: 'España', flag: '🇪🇸' },
  { code: 'MX', name: 'México', flag: '🇲🇽' },
  { code: 'CO', name: 'Colombia', flag: '🇨🇴' },
  { code: 'BR', name: 'Brasil', flag: '🇧🇷' },
];

const statuses: { value: LoanStatus; label: string }[] = [
  { value: 'PENDING', label: 'Pending' },
  { value: 'VALIDATING', label: 'Validating' },
  { value: 'IN_REVIEW', label: 'In Review' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'DISBURSED', label: 'Disbursed' },
  { value: 'CANCELLED', label: 'Cancelled' },
];

const LoanFilters = () => {
  const dispatch = useAppDispatch();
  const { filters } = useAppSelector((state) => state.loans);

  const handleCountryChange = (value: string) => {
    const countryCode = value === '' ? null : (value as CountryCode);
    dispatch(setFilters({ country_code: countryCode, page: 1 }));
    dispatch(fetchLoans({ country_code: countryCode, page: 1 }));
  };

  const handleStatusChange = (value: string) => {
    const status = value === '' ? null : (value as LoanStatus);
    dispatch(setFilters({ status, page: 1 }));
    dispatch(fetchLoans({ status, page: 1 }));
  };

  const handleReviewChange = (value: string) => {
    const requiresReview = value === '' ? null : value === 'true';
    dispatch(setFilters({ requires_review: requiresReview, page: 1 }));
    dispatch(fetchLoans({ requires_review: requiresReview, page: 1 }));
  };

  const handleClearFilters = () => {
    dispatch(clearFilters());
    dispatch(fetchLoans({ page: 1 }));
  };

  const hasActiveFilters =
    filters.country_code !== null ||
    filters.status !== null ||
    filters.requires_review !== null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex flex-wrap items-center gap-4">
        {/* Country filter */}
        <div className="flex-1 min-w-[150px]">
          <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
            Country
          </label>
          <select
            value={filters.country_code || ''}
            onChange={(e) => handleCountryChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Countries</option>
            {countries.map((country) => (
              <option key={country.code} value={country.code}>
                {country.flag} {country.name}
              </option>
            ))}
          </select>
        </div>

        {/* Status filter */}
        <div className="flex-1 min-w-[150px]">
          <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
            Status
          </label>
          <select
            value={filters.status || ''}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Statuses</option>
            {statuses.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>
        </div>

        {/* Review filter */}
        <div className="flex-1 min-w-[150px]">
          <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
            Review Status
          </label>
          <select
            value={filters.requires_review === null ? '' : String(filters.requires_review)}
            onChange={(e) => handleReviewChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All</option>
            <option value="true">Requires Review</option>
            <option value="false">No Review Needed</option>
          </select>
        </div>

        {/* Clear filters button */}
        {hasActiveFilters && (
          <div className="flex items-end">
            <Button variant="ghost" size="sm" onClick={handleClearFilters}>
              Clear Filters
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoanFilters;
