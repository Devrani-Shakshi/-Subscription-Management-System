import React from 'react';

type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

interface StatusBadgeProps {
  status: string;
  variant?: BadgeVariant;
  className?: string;
}

interface BadgeConfig {
  label: string;
  variant: BadgeVariant;
}

const STATUS_MAP: Record<string, BadgeConfig> = {
  active: { label: 'Active', variant: 'success' },
  draft: { label: 'Draft', variant: 'neutral' },
  confirmed: { label: 'Confirmed', variant: 'info' },
  closed: { label: 'Closed', variant: 'danger' },
  paid: { label: 'Paid', variant: 'success' },
  overdue: { label: 'Overdue', variant: 'danger' },
  pending: { label: 'Pending', variant: 'warning' },
  suspended: { label: 'Suspended', variant: 'danger' },
  trial: { label: 'Trial', variant: 'warning' },
  high: { label: 'High', variant: 'danger' },
  medium: { label: 'Medium', variant: 'warning' },
  low: { label: 'Low', variant: 'success' },
  cancelled: { label: 'Cancelled', variant: 'danger' },
  expired: { label: 'Expired', variant: 'neutral' },
  partial: { label: 'Partial', variant: 'warning' },
  refunded: { label: 'Refunded', variant: 'info' },
  processing: { label: 'Processing', variant: 'info' },
  completed: { label: 'Completed', variant: 'success' },
};

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  success:
    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-emerald-500/5',
  warning:
    'bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-amber-500/5',
  danger:
    'bg-red-500/10 text-red-400 border-red-500/20 shadow-red-500/5',
  info:
    'bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-blue-500/5',
  neutral:
    'bg-gray-500/10 text-gray-400 border-gray-500/20 shadow-gray-500/5',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant: overrideVariant,
  className = '',
}) => {
  const safeStatus = status || 'unknown';
  const config = STATUS_MAP[safeStatus.toLowerCase()] || {
    label: safeStatus,
    variant: 'neutral' as BadgeVariant,
  };

  const resolvedVariant = overrideVariant || config.variant;

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-0.5
        text-xs font-medium rounded-full
        border shadow-sm
        ${VARIANT_CLASSES[resolvedVariant]}
        ${className}
      `.trim()}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          resolvedVariant === 'success'
            ? 'bg-emerald-400'
            : resolvedVariant === 'warning'
            ? 'bg-amber-400'
            : resolvedVariant === 'danger'
            ? 'bg-red-400'
            : resolvedVariant === 'info'
            ? 'bg-blue-400'
            : 'bg-gray-400'
        }`}
      />
      {config.label}
    </span>
  );
};
