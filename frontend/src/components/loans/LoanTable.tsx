/**
 * Loan table component with sorting and highlighting.
 */
import { Link } from 'react-router-dom';
import type { Loan, CountryCode } from '@/types/loan';
import { StatusBadge } from '@/components/loans';
import clsx from 'clsx';

interface LoanTableProps {
  loans: Loan[];
  loading?: boolean;
}

const countries: Record<CountryCode, { name: string; flag: string }> = {
  ES: { name: 'España', flag: '🇪🇸' },
  MX: { name: 'México', flag: '🇲🇽' },
  CO: { name: 'Colombia', flag: '🇨🇴' },
  BR: { name: 'Brasil', flag: '🇧🇷' },
};

const LoanTable = ({ loans, loading = false }: LoanTableProps) => {
  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (loans.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-3">📋</div>
        <p className="text-gray-500">No loans found</p>
        <p className="text-sm text-gray-400 mt-1">Try adjusting your filters</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50">
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
              ID
            </th>
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
              Country
            </th>
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
              Applicant
            </th>
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
              Document
            </th>
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
              Amount
            </th>
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
              Risk Score
            </th>
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
              Date
            </th>
          </tr>
        </thead>
        <tbody>
          {loans.map((loan) => (
            <tr
              key={loan.id}
              className={clsx(
                'border-b border-gray-100 hover:bg-gray-50 transition-colors',
                loan.requires_review && 'bg-yellow-50 hover:bg-yellow-100'
              )}
            >
              <td className="py-3 px-4">
                <Link
                  to={`/loans/${loan.id}`}
                  className="text-primary-600 hover:underline font-mono text-sm"
                >
                  {loan.id.slice(0, 8)}...
                </Link>
                {loan.requires_review && (
                  <span className="ml-2 text-yellow-600" title="Requires review">
                    ⚠️
                  </span>
                )}
              </td>
              <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{countries[loan.country_code]?.flag}</span>
                  <span className="text-sm text-gray-500">{loan.country_code}</span>
                </div>
              </td>
              <td className="py-3 px-4">
                <div>
                  <p className="text-sm font-medium text-gray-900">{loan.full_name}</p>
                </div>
              </td>
              <td className="py-3 px-4">
                <div>
                  <span className="text-xs text-gray-500">{loan.document_type}</span>
                  <p className="text-sm font-mono text-gray-900">{loan.document_number}</p>
                </div>
              </td>
              <td className="py-3 px-4">
                <p className="text-sm font-medium text-gray-900">
                  {formatCurrency(loan.amount_requested, loan.currency)}
                </p>
                <p className="text-xs text-gray-500">{loan.currency}</p>
              </td>
              <td className="py-3 px-4">
                <StatusBadge status={loan.status} size="sm" />
              </td>
              <td className="py-3 px-4">
                {loan.risk_score !== null ? (
                  <span
                    className={clsx(
                      'text-sm font-medium',
                      loan.risk_score <= 300 && 'text-green-600',
                      loan.risk_score > 300 && loan.risk_score < 700 && 'text-yellow-600',
                      loan.risk_score >= 700 && 'text-red-600'
                    )}
                  >
                    {loan.risk_score}
                  </span>
                ) : (
                  <span className="text-sm text-gray-400">—</span>
                )}
              </td>
              <td className="py-3 px-4 text-sm text-gray-500">
                {formatDate(loan.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LoanTable;
