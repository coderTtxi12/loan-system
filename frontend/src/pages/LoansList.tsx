/**
 * Loans list page with filters and pagination.
 */
import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchLoans, setFilters } from '@/store/slices/loansSlice';
import { Card, Button } from '@/components/ui';
import { LoanTable, LoanFilters, RealTimeIndicator } from '@/components/loans';

const LoansList = () => {
  const dispatch = useAppDispatch();
  const { items, loading, pagination, filters } = useAppSelector((state) => state.loans);

  useEffect(() => {
    dispatch(fetchLoans(undefined));
  }, [dispatch]);

  const handlePageChange = (newPage: number) => {
    dispatch(setFilters({ page: newPage }));
    dispatch(fetchLoans({ page: newPage }));
  };

  const pages = Array.from({ length: pagination.total_pages }, (_, i) => i + 1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Loan Applications</h1>
          <p className="text-gray-600">
            Manage and review loan applications across all countries
          </p>
        </div>
        <div className="flex items-center gap-4">
          <RealTimeIndicator />
          <Link
            to="/loans/new"
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            + New Loan
          </Link>
        </div>
      </div>

      {/* Filters */}
      <LoanFilters />

      {/* Results info */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>
          Showing {items.length} of {pagination.total} loans
        </span>
        {(filters.country_code || filters.status || filters.requires_review !== null) && (
          <span className="text-primary-600">Filters applied</span>
        )}
      </div>

      {/* Loans table */}
      <Card padding="none">
        <LoanTable loans={items} loading={loading} />
      </Card>

      {/* Pagination */}
      {pagination.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            disabled={pagination.page <= 1}
            onClick={() => handlePageChange(pagination.page - 1)}
          >
            ← Previous
          </Button>

          <div className="flex items-center gap-1">
            {pages.map((page) => {
              // Show first, last, current, and adjacent pages
              const showPage =
                page === 1 ||
                page === pagination.total_pages ||
                Math.abs(page - pagination.page) <= 1;

              const showEllipsis =
                page === 2 && pagination.page > 3 ||
                page === pagination.total_pages - 1 && pagination.page < pagination.total_pages - 2;

              if (!showPage && !showEllipsis) return null;

              if (showEllipsis && !showPage) {
                return (
                  <span key={page} className="px-2 text-gray-400">
                    ...
                  </span>
                );
              }

              return (
                <Button
                  key={page}
                  variant={page === pagination.page ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => handlePageChange(page)}
                >
                  {page}
                </Button>
              );
            })}
          </div>

          <Button
            variant="ghost"
            size="sm"
            disabled={pagination.page >= pagination.total_pages}
            onClick={() => handlePageChange(pagination.page + 1)}
          >
            Next →
          </Button>
        </div>
      )}
    </div>
  );
};

export default LoansList;
