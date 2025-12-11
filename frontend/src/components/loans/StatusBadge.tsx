/**
 * Status badge component with color coding.
 */
import clsx from 'clsx';
import type { LoanStatus } from '@/types/loan';

interface StatusBadgeProps {
  status: LoanStatus;
  size?: 'sm' | 'md' | 'lg';
}

const statusConfig: Record<LoanStatus, { label: string; className: string }> = {
  PENDING: {
    label: 'Pending',
    className: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  },
  VALIDATING: {
    label: 'Validating',
    className: 'bg-blue-100 text-blue-800 border-blue-200',
  },
  IN_REVIEW: {
    label: 'In Review',
    className: 'bg-purple-100 text-purple-800 border-purple-200',
  },
  APPROVED: {
    label: 'Approved',
    className: 'bg-green-100 text-green-800 border-green-200',
  },
  REJECTED: {
    label: 'Rejected',
    className: 'bg-red-100 text-red-800 border-red-200',
  },
  DISBURSED: {
    label: 'Disbursed',
    className: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  },
  CANCELLED: {
    label: 'Cancelled',
    className: 'bg-gray-100 text-gray-800 border-gray-200',
  },
};

const sizeStyles = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-sm',
};

const StatusBadge = ({ status, size = 'md' }: StatusBadgeProps) => {
  const config = statusConfig[status] || statusConfig.PENDING;

  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full border',
        config.className,
        sizeStyles[size]
      )}
    >
      {config.label}
    </span>
  );
};

export default StatusBadge;
