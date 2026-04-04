import React from 'react';
import { AlertTriangle, TrendingDown, Shield } from 'lucide-react';
import { useChurnRisk } from '@/hooks/useSubscriptions';

interface ChurnRiskCardProps {
  customerId: string;
}

const LEVEL_CONFIG = {
  low: {
    icon: Shield,
    label: 'Low Risk',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20',
    barColor: 'bg-emerald-500',
  },
  medium: {
    icon: TrendingDown,
    label: 'Medium Risk',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    barColor: 'bg-amber-500',
  },
  high: {
    icon: AlertTriangle,
    label: 'High Risk',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
    barColor: 'bg-red-500',
  },
} as const;

export const ChurnRiskCard: React.FC<ChurnRiskCardProps> = ({ customerId }) => {
  const { data: churn } = useChurnRisk(customerId);

  if (!churn) return null;

  const config = LEVEL_CONFIG[churn.level];
  const Icon = config.icon;

  return (
    <div className={`rounded-xl border p-4 space-y-3 ${config.bg} ${config.border}`}>
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${config.color}`} />
        <h3 className={`text-sm font-semibold ${config.color}`}>
          {config.label}
        </h3>
      </div>

      {/* Score bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs">
          <span className="text-gray-400">Churn Score</span>
          <span className={`font-medium ${config.color}`}>
            {churn.score}%
          </span>
        </div>
        <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${config.barColor}`}
            style={{ width: `${churn.score}%` }}
          />
        </div>
      </div>

      {/* Signals */}
      {churn.signals.length > 0 && (
        <ul className="space-y-1">
          {churn.signals.map((signal, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-gray-400">
              <span className="mt-1 h-1 w-1 rounded-full bg-gray-600 shrink-0" />
              {signal}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
