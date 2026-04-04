import React from 'react';
import { Button } from './Button';

interface PageEmptyProps {
  title: string;
  message: string;
  action?: { label: string; onClick: () => void };
  className?: string;
}

export const PageEmpty: React.FC<PageEmptyProps> = ({
  title,
  message,
  action,
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center py-16 px-4 ${className}`}>
      {/* Geometric illustration */}
      <svg
        width="120"
        height="120"
        viewBox="0 0 120 120"
        fill="none"
        className="mb-6 opacity-40"
      >
        <rect
          x="20"
          y="30"
          width="80"
          height="60"
          rx="8"
          stroke="currentColor"
          strokeWidth="1.5"
          className="text-gray-600"
        />
        <line
          x1="20"
          y1="50"
          x2="100"
          y2="50"
          stroke="currentColor"
          strokeWidth="1.5"
          className="text-gray-700"
        />
        <rect
          x="30"
          y="58"
          width="25"
          height="6"
          rx="3"
          fill="currentColor"
          className="text-gray-700"
        />
        <rect
          x="30"
          y="70"
          width="40"
          height="6"
          rx="3"
          fill="currentColor"
          className="text-gray-700"
        />
        <circle
          cx="85"
          cy="40"
          r="4"
          fill="currentColor"
          className="text-violet-500/50"
        />
        <circle
          cx="60"
          cy="20"
          r="3"
          fill="currentColor"
          className="text-gray-700"
        />
        <rect
          x="50"
          y="95"
          width="20"
          height="4"
          rx="2"
          fill="currentColor"
          className="text-gray-700"
        />
      </svg>

      <h3 className="text-lg font-semibold text-gray-300 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 text-center max-w-sm mb-6">
        {message}
      </p>

      {action && (
        <Button variant="primary" size="md" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
};
