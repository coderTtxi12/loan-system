/**
 * Status timeline component showing loan history.
 */
import type { LoanStatusHistory, LoanStatus } from '@/types/loan';
import clsx from 'clsx';

interface StatusTimelineProps {
  history: LoanStatusHistory[];
  loading?: boolean;
}

const statusColors: Record<LoanStatus, string> = {
  PENDING: 'bg-yellow-500',
  VALIDATING: 'bg-blue-500',
  IN_REVIEW: 'bg-purple-500',
  APPROVED: 'bg-green-500',
  REJECTED: 'bg-red-500',
  DISBURSED: 'bg-emerald-500',
  CANCELLED: 'bg-gray-500',
};

const StatusTimeline = ({ history, loading = false }: StatusTimelineProps) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No status history available
      </div>
    );
  }

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {history.map((event, index) => (
          <li key={event.id}>
            <div className="relative pb-8">
              {/* Connecting line */}
              {index !== history.length - 1 && (
                <span
                  className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-gray-200"
                  aria-hidden="true"
                />
              )}

              <div className="relative flex space-x-3">
                {/* Status dot */}
                <div>
                  <span
                    className={clsx(
                      'h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white',
                      statusColors[event.new_status] || 'bg-gray-500'
                    )}
                  >
                    {event.new_status === 'APPROVED' && (
                      <svg className="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                    {event.new_status === 'REJECTED' && (
                      <svg className="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    )}
                    {!['APPROVED', 'REJECTED'].includes(event.new_status) && (
                      <span className="h-2 w-2 bg-white rounded-full" />
                    )}
                  </span>
                </div>

                {/* Event details */}
                <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                  <div>
                    <p className="text-sm text-gray-900">
                      {event.previous_status ? (
                        <>
                          <span className="font-medium">{event.previous_status}</span>
                          {' → '}
                          <span className="font-medium">{event.new_status}</span>
                        </>
                      ) : (
                        <>
                          Created as{' '}
                          <span className="font-medium">{event.new_status}</span>
                        </>
                      )}
                    </p>
                    {event.reason && (
                      <p className="text-sm text-gray-500 mt-0.5">
                        {event.reason}
                      </p>
                    )}
                  </div>
                  <div className="whitespace-nowrap text-right text-sm text-gray-500">
                    {formatDate(event.created_at)}
                  </div>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default StatusTimeline;
