import React from 'react';
import { AlertCircle, WifiOff } from 'lucide-react';

interface AuthErrorBannerProps {
  message: string;
  variant?: 'error' | 'warning' | 'network';
  className?: string;
}

const VARIANT_STYLES = {
  error: 'bg-red-500/10 border-red-500/20 text-red-300',
  warning: 'bg-amber-500/10 border-amber-500/20 text-amber-300',
  network: 'bg-orange-500/10 border-orange-500/20 text-orange-300',
} as const;

export const AuthErrorBanner: React.FC<AuthErrorBannerProps> = ({
  message,
  variant = 'error',
  className = '',
}) => {
  return (
    <div
      role="alert"
      className={`flex items-center gap-2.5 p-3 rounded-lg border text-sm animate-fade-in ${VARIANT_STYLES[variant]} ${className}`}
    >
      {variant === 'network' ? (
        <WifiOff className="h-4 w-4 shrink-0" />
      ) : (
        <AlertCircle className="h-4 w-4 shrink-0" />
      )}
      <span>{message}</span>
    </div>
  );
};
