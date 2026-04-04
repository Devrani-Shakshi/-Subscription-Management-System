import React, { useMemo } from 'react';

interface PasswordStrengthMeterProps {
  password: string;
  className?: string;
}

interface StrengthResult {
  score: number;
  label: string;
  color: string;
  barColor: string;
}

function computeStrength(password: string): StrengthResult {
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[a-z]/.test(password)) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  if (score <= 1) return { score, label: 'Weak', color: 'text-red-400', barColor: 'bg-red-500' };
  if (score <= 2) return { score, label: 'Fair', color: 'text-amber-400', barColor: 'bg-amber-500' };
  if (score <= 3) return { score, label: 'Good', color: 'text-blue-400', barColor: 'bg-blue-500' };
  if (score <= 4) return { score, label: 'Strong', color: 'text-emerald-400', barColor: 'bg-emerald-500' };
  return { score, label: 'Very strong', color: 'text-emerald-400', barColor: 'bg-emerald-500' };
}

export const PasswordStrengthMeter: React.FC<PasswordStrengthMeterProps> = ({
  password,
  className = '',
}) => {
  const strength = useMemo(() => computeStrength(password), [password]);
  const maxSegments = 5;

  if (!password) return null;

  return (
    <div className={`space-y-1 ${className}`}>
      <div className="flex gap-1">
        {Array.from({ length: maxSegments }).map((_, i) => (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full transition-colors duration-300 ${
              i < strength.score ? strength.barColor : 'bg-gray-700'
            }`}
          />
        ))}
      </div>
      <p className={`text-xs font-medium ${strength.color}`}>
        {strength.label}
      </p>
    </div>
  );
};
