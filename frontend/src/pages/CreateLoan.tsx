/**
 * Create loan form page.
 */
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAppDispatch } from '@/store/hooks';
import { createLoan } from '@/store/slices/loansSlice';
import { addNotification } from '@/store/slices/uiSlice';
import { LoanForm } from '@/components/loans';
import type { LoanCreateRequest } from '@/types/loan';

interface ErrorInfo {
  message: string;
  errors?: string[];
}

const CreateLoan = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ErrorInfo | null>(null);

  const handleSubmit = async (data: LoanCreateRequest) => {
    setLoading(true);
    setError(null);

    try {
      const result = await dispatch(createLoan(data)).unwrap();
      
      dispatch(
        addNotification({
          type: 'success',
          message: 'Loan application created successfully!',
          duration: 5000,
        })
      );

      // Redirect to the new loan's detail page
      navigate(`/loans/${result.id}`);
    } catch (err: any) {
      // Handle error object with message from rejectWithValue
      // err can be either { message, errors } object or a string (legacy)
      let errorInfo: ErrorInfo;
      
      if (typeof err === 'string') {
        errorInfo = { message: err };
      } else if (err?.message) {
        errorInfo = {
          message: err.message,
          errors: err.errors || [],
        };
      } else {
        errorInfo = { message: 'Failed to create loan application' };
      }
      
      setError(errorInfo);
      
      dispatch(
        addNotification({
          type: 'error',
          message: errorInfo.message,
          duration: 5000,
        })
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <Link
            to="/loans"
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            ← Back to Loans
          </Link>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Create Loan Application</h1>
        <p className="text-gray-600">
          Fill out the form below to create a new loan application
        </p>
      </div>

      {/* Error message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-2">
            <span className="text-red-500">❌</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-red-700">{error.message}</p>
              {error.errors && error.errors.length > 0 && (
                <ul className="mt-2 ml-4 list-disc space-y-1">
                  {error.errors.map((err, index) => (
                    <li key={index} className="text-sm text-red-600">
                      {err}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Form */}
      <LoanForm onSubmit={handleSubmit} loading={loading} />
    </div>
  );
};

export default CreateLoan;
