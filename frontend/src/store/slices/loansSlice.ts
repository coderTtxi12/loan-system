/**
 * Loans slice for loan state management.
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import type { 
  Loan, 
  LoanCreateRequest, 
  LoansState, 
  LoanFilters,
  LoanStatistics 
} from '@/types/loan';
import { api } from '@/services/api';

// Initial state
const initialState: LoansState = {
  items: [],
  selectedLoan: null,
  statistics: null,
  loading: false,
  error: null,
  filters: {
    country_code: null,
    status: null,
    requires_review: null,
    page: 1,
    page_size: 20,
  },
  pagination: {
    total: 0,
    page: 1,
    page_size: 20,
    total_pages: 0,
  },
};

// Async thunks
export const fetchLoans = createAsyncThunk(
  'loans/fetchLoans',
  async (filters: Partial<LoanFilters> | undefined, { getState, rejectWithValue }) => {
    try {
      const state = getState() as { loans: LoansState };
      const currentFilters = { ...state.loans.filters, ...filters };
      
      const params = new URLSearchParams();
      if (currentFilters.country_code) params.append('country_code', currentFilters.country_code);
      if (currentFilters.status) params.append('status', currentFilters.status);
      if (currentFilters.requires_review !== null) {
        params.append('requires_review', String(currentFilters.requires_review));
      }
      params.append('page', String(currentFilters.page));
      params.append('page_size', String(currentFilters.page_size));
      
      const response = await api.get(`/loans?${params.toString()}`);
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.message || 'Failed to fetch loans';
      return rejectWithValue(message);
    }
  }
);

export const fetchLoanById = createAsyncThunk(
  'loans/fetchLoanById',
  async (loanId: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/loans/${loanId}`);
      return response.data as Loan;
    } catch (error: any) {
      const message = error.response?.data?.message || 'Failed to fetch loan';
      return rejectWithValue(message);
    }
  }
);

export const createLoan = createAsyncThunk(
  'loans/createLoan',
  async (loanData: LoanCreateRequest, { rejectWithValue }) => {
    try {
      const response = await api.post('/loans', loanData);
      return response.data as Loan;
    } catch (error: any) {
      // Log full error for debugging
      console.error('Create loan error:', {
        status: error.response?.status,
        data: error.response?.data,
        request: loanData,
      });
      
      // Extract detailed error message and errors array
      const errorData = error.response?.data;
      let message = 'Failed to create loan';
      let errors: string[] = [];
      
      if (errorData?.detail) {
        // FastAPI validation errors
        if (Array.isArray(errorData.detail)) {
          errors = errorData.detail.map((err: any) => 
            `${err.loc?.join('.')}: ${err.msg}`
          );
          message = `Validation error: ${errors.join(', ')}`;
        } else if (typeof errorData.detail === 'object') {
          // Custom API exception format: { message, errors }
          message = errorData.detail.message || message;
          errors = errorData.detail.errors || [];
        } else if (typeof errorData.detail === 'string') {
          message = errorData.detail;
        }
      } else if (errorData?.message) {
        message = errorData.message;
      }
      
      // Return object with both message and errors
      return rejectWithValue({ message, errors });
    }
  }
);

export const updateLoanStatus = createAsyncThunk(
  'loans/updateStatus',
  async (
    { loanId, status, reason }: { loanId: string; status: string; reason?: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await api.patch(`/loans/${loanId}/status`, { status, reason });
      return response.data as Loan;
    } catch (error: any) {
      const message = error.response?.data?.message || 'Failed to update status';
      return rejectWithValue(message);
    }
  }
);

export const fetchLoanHistory = createAsyncThunk(
  'loans/fetchHistory',
  async (loanId: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/loans/${loanId}/history`);
      return { loanId, history: response.data };
    } catch (error: any) {
      const message = error.response?.data?.message || 'Failed to fetch history';
      return rejectWithValue(message);
    }
  }
);

export const fetchStatistics = createAsyncThunk(
  'loans/fetchStatistics',
  async (countryCode: string | undefined, { rejectWithValue }) => {
    try {
      const url = countryCode ? `/loans/statistics?country_code=${countryCode}` : '/loans/statistics';
      const response = await api.get(url);
      return response.data as LoanStatistics;
    } catch (error: any) {
      const message = error.response?.data?.message || 'Failed to fetch statistics';
      return rejectWithValue(message);
    }
  }
);

// Slice
const loansSlice = createSlice({
  name: 'loans',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<Partial<LoanFilters>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = initialState.filters;
    },
    clearSelectedLoan: (state) => {
      state.selectedLoan = null;
    },
    clearError: (state) => {
      state.error = null;
    },
    // For real-time updates via Socket.IO
    loanUpdated: (state, action: PayloadAction<Partial<Loan> & { id: string }>) => {
      const index = state.items.findIndex((l) => l.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = { ...state.items[index], ...action.payload };
      }
      if (state.selectedLoan?.id === action.payload.id) {
        state.selectedLoan = { ...state.selectedLoan, ...action.payload };
      }
    },
    loanCreated: (state, action: PayloadAction<Loan>) => {
      state.items.unshift(action.payload);
      state.pagination.total += 1;
    },
    statusChanged: (
      state,
      action: PayloadAction<{ loan_id: string; old_status: string; new_status: string }>
    ) => {
      const { loan_id, new_status } = action.payload;
      const index = state.items.findIndex((l) => l.id === loan_id);
      if (index !== -1) {
        state.items[index].status = new_status as any;
      }
      if (state.selectedLoan?.id === loan_id) {
        state.selectedLoan.status = new_status as any;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch loans
    builder
      .addCase(fetchLoans.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchLoans.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.pagination = {
          total: action.payload.total,
          page: action.payload.page,
          page_size: action.payload.page_size,
          total_pages: action.payload.total_pages,
        };
      })
      .addCase(fetchLoans.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch loan by ID
    builder
      .addCase(fetchLoanById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchLoanById.fulfilled, (state, action) => {
        state.loading = false;
        state.selectedLoan = action.payload;
      })
      .addCase(fetchLoanById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Create loan
    builder
      .addCase(createLoan.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createLoan.fulfilled, (state, action) => {
        state.loading = false;
        state.items.unshift(action.payload);
        state.pagination.total += 1;
      })
      .addCase(createLoan.rejected, (state, action) => {
        state.loading = false;
        // Handle both string (legacy) and object (new format) error payloads
        const payload = action.payload as any;
        state.error = typeof payload === 'string' 
          ? payload 
          : payload?.message || 'Failed to create loan';
      });

    // Update status
    builder
      .addCase(updateLoanStatus.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateLoanStatus.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.items.findIndex((l) => l.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
        if (state.selectedLoan?.id === action.payload.id) {
          state.selectedLoan = action.payload;
        }
      })
      .addCase(updateLoanStatus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch statistics
    builder
      .addCase(fetchStatistics.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.statistics = action.payload;
      })
      .addCase(fetchStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  setFilters,
  clearFilters,
  clearSelectedLoan,
  clearError,
  loanUpdated,
  loanCreated,
  statusChanged,
} = loansSlice.actions;

export default loansSlice.reducer;
