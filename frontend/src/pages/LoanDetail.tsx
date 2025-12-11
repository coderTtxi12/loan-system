/**
 * Loan detail page.
 * Will be fully implemented in Commit 30.
 */
import { useParams } from 'react-router-dom';

const LoanDetail = () => {
  const { id } = useParams<{ id: string }>();
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Loan Detail</h1>
      <p className="text-gray-600">Loan ID: {id}</p>
      <p className="text-gray-600">Full detail view - Coming in Commit 30</p>
    </div>
  );
};

export default LoanDetail;
