import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import * as LucideIcons from 'lucide-react';

type StatColor = 'violet' | 'teal' | 'amber' | 'rose' | 'blue';

interface StatCardProps {
  label: string;
  value: string | number;
  change?: { value: number; positive: boolean };
  icon?: string;
  color?: StatColor;
  className?: string;
}

const COLOR_MAP: Record<StatColor, { bg: string; icon: string; glow: string }> = {
  violet: {
    bg: 'bg-violet-500/10 border-violet-500/20',
    icon: 'text-violet-400',
    glow: 'shadow-violet-500/5',
  },
  teal: {
    bg: 'bg-teal-500/10 border-teal-500/20',
    icon: 'text-teal-400',
    glow: 'shadow-teal-500/5',
  },
  amber: {
    bg: 'bg-amber-500/10 border-amber-500/20',
    icon: 'text-amber-400',
    glow: 'shadow-amber-500/5',
  },
  rose: {
    bg: 'bg-rose-500/10 border-rose-500/20',
    icon: 'text-rose-400',
    glow: 'shadow-rose-500/5',
  },
  blue: {
    bg: 'bg-blue-500/10 border-blue-500/20',
    icon: 'text-blue-400',
    glow: 'shadow-blue-500/5',
  },
};

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  change,
  icon,
  color = 'violet',
  className = '',
}) => {
  const colors = COLOR_MAP[color];
  const icons = LucideIcons as unknown as Record<string, React.FC<{ className?: string }>>;
  const IconComponent = icon ? icons[icon] : null;

  return (
    <div
      className={`
        bg-gray-900 border border-gray-800 rounded-xl p-4
        hover:border-gray-700 transition-all duration-300
        shadow-lg ${colors.glow}
        ${className}
      `.trim()}
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-sm font-medium text-gray-400">{label}</span>
        {IconComponent && (
          <div
            className={`h-9 w-9 rounded-lg border flex items-center justify-center ${colors.bg}`}
          >
            <IconComponent className={`h-4 w-4 ${colors.icon}`} />
          </div>
        )}
      </div>

      <div className="text-2xl font-bold text-gray-50 tracking-tight">
        {value}
      </div>

      {change && (
        <div
          className={`flex items-center gap-1 mt-2 text-sm font-medium ${
            change.positive ? 'text-emerald-400' : 'text-red-400'
          }`}
        >
          {change.positive ? (
            <TrendingUp className="h-3.5 w-3.5" />
          ) : (
            <TrendingDown className="h-3.5 w-3.5" />
          )}
          <span>
            {change.positive ? '+' : ''}
            {change.value}%
          </span>
          <span className="text-gray-500 font-normal">vs last period</span>
        </div>
      )}
    </div>
  );
};
