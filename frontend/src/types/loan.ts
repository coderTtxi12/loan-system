/**
 * Loan types.
 */

export type LoanStatus =
  | 'PENDING'
  | 'VALIDATING'
  | 'IN_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'DISBURSED'
  | 'CANCELLED';

export type CountryCode = 'ES' | 'MX' | 'CO' | 'BR';

export type DocumentType = 'DNI' | 'CURP' | 'CC' | 'CPF';

export interface BankingInfo {
  provider: string;
  loan_score: number | null;
  total_debt: number | null;
  active_loans: number;
  payment_history: string | null;
}

export interface Loan {
  id: string;
  country_code: CountryCode;
  document_type: DocumentType;
  document_number: string;
  full_name: string;
  amount_requested: number;
  currency: string;
  monthly_income: number;
  status: LoanStatus;
  risk_score: number | null;
  requires_review: boolean;
  banking_info: BankingInfo | null;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  created_by_id: string | null;
  reviewed_by_id: string | null;
}

export interface LoanCreateRequest {
  country_code: CountryCode;
  document_type: DocumentType;
  document_number: string;
  full_name: string;
  amount_requested: number;
  monthly_income: number;
}

export interface LoanStatusUpdate {
  status: LoanStatus;
  reason?: string;
}

export interface LoanStatusHistory {
  id: number;
  loan_id: string;
  previous_status: LoanStatus | null;
  new_status: LoanStatus;
  reason: string | null;
  changed_by_id: string | null;
  created_at: string;
}

export interface LoanFilters {
  country_code: CountryCode | null;
  status: LoanStatus | null;
  requires_review: boolean | null;
  page: number;
  page_size: number;
}

export interface LoanPagination {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface LoanStatistics {
  total_loans: number;
  by_status: Record<LoanStatus, number>;
  by_country: Record<CountryCode, number>;
  total_amount_requested: number;
  average_risk_score: number | null;
  pending_review_count: number;
}

export interface LoansState {
  items: Loan[];
  selectedLoan: Loan | null;
  statistics: LoanStatistics | null;
  loading: boolean;
  error: string | null;
  filters: LoanFilters;
  pagination: LoanPagination;
}
