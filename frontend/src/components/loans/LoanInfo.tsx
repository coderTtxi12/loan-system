/**
 * Loan information display component.
 */
import type { Loan, CountryCode } from '@/types/loan';
import { StatusBadge } from '@/components/loans';

interface LoanInfoProps {
  loan: Loan;
}

const countries: Record<CountryCode, { name: string; flag: string }> = {
  ES: { name: 'España', flag: '🇪🇸' },
  MX: { name: 'México', flag: '🇲🇽' },
  CO: { name: 'Colombia', flag: '🇨🇴' },
  BR: { name: 'Brasil', flag: '🇧🇷' },
};

const LoanInfo = ({ loan }: LoanInfoProps) => {
  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const InfoRow = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div className="flex justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-900">{children}</span>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Status Section */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">Current Status</p>
            <div className="mt-1">
              <StatusBadge status={loan.status} size="lg" />
            </div>
          </div>
          {loan.risk_score !== null && (
            <div className="text-right">
              <p className="text-sm text-gray-500">Risk Score</p>
              <p className="text-2xl font-bold text-gray-900">{loan.risk_score}</p>
            </div>
          )}
        </div>
        {loan.requires_review && (
          <div className="mt-3 p-2 bg-yellow-100 rounded text-sm text-yellow-800">
            ⚠️ This loan requires manual review
          </div>
        )}
      </div>

      {/* Applicant Information */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 uppercase mb-3">
          Applicant Information
        </h3>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <InfoRow label="Full Name">{loan.full_name}</InfoRow>
          <InfoRow label="Email">{loan.email}</InfoRow>
          <InfoRow label="Document Type">{loan.document_type}</InfoRow>
          <InfoRow label="Document Number">
            <span className="font-mono">{loan.document_number}</span>
          </InfoRow>
        </div>
      </div>

      {/* Loan Details */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 uppercase mb-3">
          Loan Details
        </h3>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <InfoRow label="Country">
            <span className="flex items-center gap-2">
              <span className="text-lg">{countries[loan.country_code]?.flag}</span>
              {countries[loan.country_code]?.name}
            </span>
          </InfoRow>
          <InfoRow label="Amount Requested">
            {formatCurrency(loan.amount_requested, loan.currency)}
          </InfoRow>
          <InfoRow label="Currency">{loan.currency}</InfoRow>
          <InfoRow label="Monthly Income">
            {formatCurrency(loan.monthly_income, loan.currency)}
          </InfoRow>
        </div>
      </div>

      {/* Banking Information */}
      {loan.banking_info && (
        <div>
          <h3 className="text-sm font-semibold text-gray-900 uppercase mb-3">
            Banking Information
          </h3>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <InfoRow label="Provider">{loan.banking_info.provider}</InfoRow>
            {loan.banking_info.loan_score !== null && (
              <InfoRow label="Credit Score">{loan.banking_info.loan_score}</InfoRow>
            )}
            {loan.banking_info.total_debt !== null && (
              <InfoRow label="Total Debt">
                {formatCurrency(loan.banking_info.total_debt, loan.currency)}
              </InfoRow>
            )}
            <InfoRow label="Active Loans">{loan.banking_info.active_loans}</InfoRow>
            {loan.banking_info.payment_history && (
              <InfoRow label="Payment History">{loan.banking_info.payment_history}</InfoRow>
            )}
          </div>
        </div>
      )}

      {/* Timestamps */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 uppercase mb-3">
          Timeline
        </h3>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <InfoRow label="Created">{formatDate(loan.created_at)}</InfoRow>
          <InfoRow label="Last Updated">{formatDate(loan.updated_at)}</InfoRow>
        </div>
      </div>
    </div>
  );
};

export default LoanInfo;
