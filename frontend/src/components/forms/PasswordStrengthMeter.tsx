import React, { useMemo } from 'react';

interface PasswordStrengthMeterProps {
  password: string;
  className?: string;
}

type StrengthLevel = 'weak' | 'fair' | 'good' | 'strong';

interface StrengthInfo {
  level: StrengthLevel;
  score: number;
  label: string;
  color: string;
}

function computeStrength(password: string): StrengthInfo {
  let score = 0;
  if (password.length >= 8) score++;
  if (/[a-z]/.test(password)) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  const levels: Record<number, StrengthInfo> = {
    0: { level: 'weak', score: 0, label: 'Weak', color: 'bg-red-500' },
    1: { level: 'weak', score: 1, label: 'Weak', color: 'bg-red-500' },
    2: { level: 'fair', score: 2, label: 'Fair', color: 'bg-amber-500' },
    3: { level: 'good', score: 3, label: 'Good', color: 'bg-teal-400' },
    4: { level: 'strong', score: 4, label: 'Strong', color: 'bg-green-400' },
  };

  return levels[score];
}

export const PasswordStrengthMeter: React.FC<PasswordStrengthMeterProps> = ({
  password,
  className = '',
}) => {
  const strength = useMemo(() => computeStrength(password), [password]);

  if (!password) return null;

  return (
    <div className={`space-y-1.5 ${className}`}>
      {/* 4-segment bar */}
      <div className="flex gap-1">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-all duration-300 ${
              i < strength.score ? strength.color : 'bg-gray-800'
            }`}
          />
        ))}
      </div>
      <p
        className={`text-xs transition-colors duration-200 ${
          strength.score <= 1
            ? 'text-red-400'
            : strength.score === 2
              ? 'text-amber-400'
              : strength.score === 3
                ? 'text-teal-400'
                : 'text-green-400'
        }`}
      >
        {strength.label}
      </p>
    </div>
  );
};
