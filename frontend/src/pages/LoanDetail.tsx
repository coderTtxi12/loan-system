/**
 * Loan detail page with full information and status management.
 */
import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchLoanById, updateLoanStatus, fetchLoanHistory, clearSelectedLoan } from '@/store/slices/loansSlice';
import { Card, Button } from '@/components/ui';
import { 
  LoanInfo, 
  StatusTimeline, 
  StatusChangeModal, 
  RealTimeIndicator 
} from '@/components/loans';
import { subscribeToLoan, unsubscribeFromLoan } from '@/services/socket';
import type { LoanStatus, LoanStatusHistory } from '@/types/loan';

const LoanDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { selectedLoan, loading, error } = useAppSelector((state) => state.loans);
  const { user } = useAppSelector((state) => state.auth);
  
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);
  const [history, setHistory] = useState<LoanStatusHistory[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Fetch loan on mount
  useEffect(() => {
    if (id) {
      dispatch(fetchLoanById(id));
      
      // Subscribe to real-time updates
      subscribeToLoan(id);
    }

    return () => {
      dispatch(clearSelectedLoan());
      if (id) {
        unsubscribeFromLoan(id);
      }
    };
  }, [dispatch, id]);

  // Fetch history
  useEffect(() => {
    const loadHistory = async () => {
      if (id) {
        setHistoryLoading(true);
        try {
          const result = await dispatch(fetchLoanHistory(id)).unwrap();
          setHistory(result.history || []);
        } catch {
          setHistory([]);
        } finally {
          setHistoryLoading(false);
        }
      }
    };
    loadHistory();
  }, [dispatch, id, selectedLoan?.status]);

  const handleStatusChange = async (newStatus: LoanStatus, reason: string) => {
    if (!id) return;
    
    setStatusLoading(true);
    try {
      await dispatch(updateLoanStatus({ loanId: id, status: newStatus, reason })).unwrap();
      setShowStatusModal(false);
      // Refresh history
      const result = await dispatch(fetchLoanHistory(id)).unwrap();
      setHistory(result.history || []);
    } finally {
      setStatusLoading(false);
    }
  };

  const canChangeStatus = user?.role === 'ADMIN' || user?.role === 'ANALYST';

  if (loading && !selectedLoan) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">❌</div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Loan</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <Button onClick={() => navigate('/loans')}>Back to Loans</Button>
      </div>
    );
  }

  if (!selectedLoan) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">🔍</div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Loan Not Found</h2>
        <p className="text-gray-600 mb-4">The requested loan could not be found.</p>
        <Button onClick={() => navigate('/loans')}>Back to Loans</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Link
              to="/loans"
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              ← Back to Loans
            </Link>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Loan Details</h1>
          <p className="text-gray-600 font-mono text-sm">{selectedLoan.id}</p>
        </div>
        <div className="flex items-center gap-4">
          <RealTimeIndicator />
          {canChangeStatus && (
            <Button onClick={() => setShowStatusModal(true)}>
              Change Status
            </Button>
          )}
        </div>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info - 2 columns */}
        <div className="lg:col-span-2">
          <Card title="Loan Information">
            <LoanInfo loan={selectedLoan} />
          </Card>
        </div>

        {/* Status Timeline - 1 column */}
        <div>
          <Card title="Status History">
            <StatusTimeline history={history} loading={historyLoading} />
          </Card>
        </div>
      </div>

      {/* Status Change Modal */}
      <StatusChangeModal
        isOpen={showStatusModal}
        onClose={() => setShowStatusModal(false)}
        onConfirm={handleStatusChange}
        currentStatus={selectedLoan.status}
        loading={statusLoading}
      />
    </div>
  );
};

export default LoanDetail;
