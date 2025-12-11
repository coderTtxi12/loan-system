/**
 * Dashboard page with statistics and recent loans.
 */
import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchLoans, fetchStatistics } from '@/store/slices/loansSlice';
import { Card } from '@/components/ui';
import { StatusBadge } from '@/components/loans';
import type { LoanStatus, CountryCode } from '@/types/loan';

// Country info
const countries: Record<CountryCode, { name: string; flag: string }> = {
  ES: { name: 'España', flag: '🇪🇸' },
  MX: { name: 'México', flag: '🇲🇽' },
  CO: { name: 'Colombia', flag: '🇨🇴' },
  BR: { name: 'Brasil', flag: '🇧🇷' },
};

// Status info
const statuses: { status: LoanStatus; label: string; color: string }[] = [
  { status: 'PENDING', label: 'Pending', color: 'bg-yellow-500' },
  { status: 'IN_REVIEW', label: 'In Review', color: 'bg-purple-500' },
  { status: 'APPROVED', label: 'Approved', color: 'bg-green-500' },
  { status: 'REJECTED', label: 'Rejected', color: 'bg-red-500' },
];

const Dashboard = () => {
  const dispatch = useAppDispatch();
  const { items, statistics, loading } = useAppSelector((state) => state.loans);

  useEffect(() => {
    dispatch(fetchStatistics(undefined));
    dispatch(fetchLoans({ page: 1, page_size: 5 }));
  }, [dispatch]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Overview of loan applications</p>
        </div>
        <Link
          to="/loans/new"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          + New Loan
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Loans */}
        <Card className="bg-gradient-to-br from-primary-500 to-primary-600 text-white border-0">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-primary-100 text-sm">Total Loans</p>
              <p className="text-3xl font-bold mt-1">
                {statistics?.total_loans ?? 0}
              </p>
            </div>
            <div className="text-4xl opacity-80">📊</div>
          </div>
        </Card>

        {/* Total Amount */}
        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white border-0">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm">Total Requested</p>
              <p className="text-3xl font-bold mt-1">
                {formatCurrency(statistics?.total_amount_requested ?? 0)}
              </p>
            </div>
            <div className="text-4xl opacity-80">💰</div>
          </div>
        </Card>

        {/* Pending Review */}
        <Card className="bg-gradient-to-br from-yellow-500 to-orange-500 text-white border-0">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-yellow-100 text-sm">Pending Review</p>
              <p className="text-3xl font-bold mt-1">
                {statistics?.pending_review_count ?? 0}
              </p>
            </div>
            <div className="text-4xl opacity-80">⏳</div>
          </div>
        </Card>

        {/* Avg Risk Score */}
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm">Avg Risk Score</p>
              <p className="text-3xl font-bold mt-1">
                {statistics?.average_risk_score?.toFixed(0) ?? 'N/A'}
              </p>
            </div>
            <div className="text-4xl opacity-80">📈</div>
          </div>
        </Card>
      </div>

      {/* Status and Country Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By Status */}
        <Card title="Loans by Status">
          <div className="space-y-3">
            {statuses.map(({ status, label, color }) => {
              const count = statistics?.by_status?.[status] ?? 0;
              const percentage = statistics?.total_loans
                ? Math.round((count / statistics.total_loans) * 100)
                : 0;
              return (
                <div key={status} className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${color}`} />
                  <span className="flex-1 text-sm text-gray-700">{label}</span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${color}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-10 text-right">
                    {percentage}%
                  </span>
                </div>
              );
            })}
          </div>
        </Card>

        {/* By Country */}
        <Card title="Loans by Country">
          <div className="space-y-3">
            {Object.entries(countries).map(([code, { name, flag }]) => {
              const count = statistics?.by_country?.[code as CountryCode] ?? 0;
              const percentage = statistics?.total_loans
                ? Math.round((count / statistics.total_loans) * 100)
                : 0;
              return (
                <div key={code} className="flex items-center gap-3">
                  <span className="text-xl">{flag}</span>
                  <span className="flex-1 text-sm text-gray-700">{name}</span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-primary-500"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-10 text-right">
                    {percentage}%
                  </span>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Recent Loans */}
      <Card title="Recent Loans" subtitle="Last 5 loan applications">
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          </div>
        ) : items.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No loans yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    ID
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Country
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Amount
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.slice(0, 5).map((loan) => (
                  <tr
                    key={loan.id}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-3 px-4">
                      <Link
                        to={`/loans/${loan.id}`}
                        className="text-primary-600 hover:underline font-mono text-sm"
                      >
                        {loan.id.slice(0, 8)}...
                      </Link>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-lg">
                        {countries[loan.country_code]?.flag}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-900">
                      {loan.full_name}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-900">
                      {formatCurrency(loan.amount_requested)} {loan.currency}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={loan.status} size="sm" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <Link
            to="/loans"
            className="text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            View all loans →
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;
