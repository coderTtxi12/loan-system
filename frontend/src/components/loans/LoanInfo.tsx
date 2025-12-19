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
            {(loan.banking_info.provider_name || loan.banking_info.provider) && (
              <InfoRow label="Provider">
                {loan.banking_info.provider_name || loan.banking_info.provider}
              </InfoRow>
            )}
            {(loan.banking_info.credit_score !== null && loan.banking_info.credit_score !== undefined) && (
              <InfoRow label="Credit Score">{loan.banking_info.credit_score}</InfoRow>
            )}
            {(loan.banking_info.loan_score !== null && loan.banking_info.loan_score !== undefined && !loan.banking_info.credit_score) && (
              <InfoRow label="Credit Score">{loan.banking_info.loan_score}</InfoRow>
            )}
            {loan.banking_info.total_debt !== null && loan.banking_info.total_debt !== undefined && (
              <InfoRow label="Total Debt">
                {formatCurrency(
                  typeof loan.banking_info.total_debt === 'string' 
                    ? parseFloat(loan.banking_info.total_debt) 
                    : loan.banking_info.total_debt,
                  loan.currency
                )}
              </InfoRow>
            )}
            {loan.banking_info.monthly_obligations !== null && loan.banking_info.monthly_obligations !== undefined && (
              <InfoRow label="Monthly Obligations">
                {formatCurrency(
                  typeof loan.banking_info.monthly_obligations === 'string'
                    ? parseFloat(loan.banking_info.monthly_obligations)
                    : loan.banking_info.monthly_obligations,
                  loan.currency
                )}
              </InfoRow>
            )}
            {loan.banking_info.available_credit !== null && loan.banking_info.available_credit !== undefined && (
              <InfoRow label="Available Credit">
                {formatCurrency(
                  typeof loan.banking_info.available_credit === 'string'
                    ? parseFloat(loan.banking_info.available_credit)
                    : loan.banking_info.available_credit,
                  loan.currency
                )}
              </InfoRow>
            )}
            {loan.banking_info.account_age_months !== null && loan.banking_info.account_age_months !== undefined && (
              <InfoRow label="Account Age">
                {loan.banking_info.account_age_months} months
              </InfoRow>
            )}
            {loan.banking_info.payment_history_score !== null && loan.banking_info.payment_history_score !== undefined && (
              <InfoRow label="Payment History Score">
                {loan.banking_info.payment_history_score}/100
              </InfoRow>
            )}
            {loan.banking_info.payment_history && (
              <InfoRow label="Payment History">{loan.banking_info.payment_history}</InfoRow>
            )}
            {loan.banking_info.has_defaults !== undefined && (
              <InfoRow label="Has Defaults">
                <span className={loan.banking_info.has_defaults ? 'text-red-600 font-semibold' : 'text-green-600'}>
                  {loan.banking_info.has_defaults ? 'Yes' : 'No'}
                </span>
              </InfoRow>
            )}
            {loan.banking_info.default_count !== undefined && loan.banking_info.default_count > 0 && (
              <InfoRow label="Default Count">
                <span className="text-red-600 font-semibold">{loan.banking_info.default_count}</span>
              </InfoRow>
            )}
            {loan.banking_info.income_verified !== undefined && (
              <InfoRow label="Income Verified">
                <span className={loan.banking_info.income_verified ? 'text-green-600' : 'text-gray-500'}>
                  {loan.banking_info.income_verified ? '✓ Verified' : '✗ Not Verified'}
                </span>
              </InfoRow>
            )}
            {loan.banking_info.employment_verified !== undefined && (
              <InfoRow label="Employment Verified">
                <span className={loan.banking_info.employment_verified ? 'text-green-600' : 'text-gray-500'}>
                  {loan.banking_info.employment_verified ? '✓ Verified' : '✗ Not Verified'}
                </span>
              </InfoRow>
            )}
            {loan.banking_info.active_loans !== undefined && (
              <InfoRow label="Active Loans">{loan.banking_info.active_loans}</InfoRow>
            )}
          </div>
        </div>
      )}

      {/* Risk Factors & Warnings */}
      {loan.extra_data && (
        <div>
          <h3 className="text-sm font-semibold text-gray-900 uppercase mb-3">
            Risk Analysis
          </h3>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            {loan.extra_data.risk_factors && Object.keys(loan.extra_data.risk_factors).length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Risk Factors:</p>
                <div className="space-y-1">
                  {Object.entries(loan.extra_data.risk_factors).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="text-gray-600 capitalize">
                        {key.replace(/_/g, ' ')}:
                      </span>
                      <span className="text-gray-900 font-medium">
                        {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : 
                         typeof value === 'number' && value < 1 ? `${(value * 100).toFixed(1)}%` :
                         String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {loan.extra_data.validation_warnings && loan.extra_data.validation_warnings.length > 0 && (
              <div>
                <p className="text-sm font-medium text-yellow-700 mb-2">Validation Warnings:</p>
                <ul className="list-disc list-inside space-y-1">
                  {loan.extra_data.validation_warnings.map((warning, index) => (
                    <li key={index} className="text-sm text-yellow-600">
                      {warning}
                    </li>
                  ))}
                </ul>
              </div>
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
          {loan.processed_at && (
            <InfoRow label="Processed">{formatDate(loan.processed_at)}</InfoRow>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoanInfo;
