import React from 'react';

interface ProgressBarProps {
  value: number;
  max: number;
  label?: string;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max,
  label,
  className = '',
}) => {
  const percentage = max > 0 ? Math.min((value / max) * 100, 100) : 0;

  const colorClass =
    percentage >= 90
      ? 'bg-red-500'
      : percentage >= 70
      ? 'bg-amber-500'
      : 'bg-violet-500';

  return (
    <div className={`space-y-1 ${className}`}>
      {label && (
        <span className="text-xs text-gray-400">{label}</span>
      )}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${colorClass}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="text-xs text-gray-400 tabular-nums shrink-0">
          {value}/{max}
        </span>
      </div>
    </div>
  );
};
