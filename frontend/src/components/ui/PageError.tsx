import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface PageErrorProps {
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const PageError: React.FC<PageErrorProps> = ({
  message = 'Something went wrong. Please try again.',
  onRetry,
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center py-16 px-4 ${className}`}>
      <div className="h-16 w-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-6">
        <AlertTriangle className="h-8 w-8 text-red-400" />
      </div>
      <h3 className="text-lg font-semibold text-gray-300 mb-1">
        Error occurred
      </h3>
      <p className="text-sm text-gray-500 text-center max-w-sm mb-6">
        {message}
      </p>
      {onRetry && (
        <Button
          variant="secondary"
          size="md"
          onClick={onRetry}
          icon={<RefreshCw className="h-4 w-4" />}
        >
          Try again
        </Button>
      )}
    </div>
  );
};
