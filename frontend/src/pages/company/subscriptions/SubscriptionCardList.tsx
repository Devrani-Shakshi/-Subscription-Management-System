import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { StatusBadge } from '@/components/ui';
import { formatDate, formatCurrency } from '@/lib/utils';
import type { SubscriptionSummary } from '@/types/subscription';

interface SubscriptionCardListProps {
  subscriptions: SubscriptionSummary[];
  selected: string[];
  onSelect: (id: string) => void;
}

export const SubscriptionCardList: React.FC<SubscriptionCardListProps> = ({
  subscriptions,
  selected,
  onSelect,
}) => {
  const navigate = useNavigate();

  if (subscriptions.length === 0) return null;

  return (
    <div className="lg:hidden space-y-3">
      {subscriptions.map((sub) => (
        <div
          key={sub.id}
          onClick={() => navigate(`/company/subscriptions/${sub.id}`)}
          className="bg-gray-900 border border-gray-800 rounded-xl p-4
                     flex items-center gap-3 cursor-pointer
                     hover:border-gray-700 active:bg-gray-800/50
                     transition-all duration-200"
        >
          <input
            type="checkbox"
            checked={selected.includes(sub.id)}
            onChange={(e) => {
              e.stopPropagation();
              onSelect(sub.id);
            }}
            onClick={(e) => e.stopPropagation()}
            className="h-4 w-4 rounded border-gray-600 bg-gray-800 text-violet-500
                       focus:ring-violet-500/40 cursor-pointer shrink-0"
          />

          <div className="flex-1 min-w-0 space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-violet-400 shrink-0">
                {sub.number}
              </span>
              <span className="text-sm font-medium text-gray-100 truncate">
                {sub.customerName}
              </span>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center px-1.5 py-0.5 rounded
                               bg-violet-500/10 text-violet-300 text-xs font-medium">
                {sub.planName}
              </span>
              <StatusBadge status={sub.status} />
            </div>
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Expires {formatDate(sub.expiryDate)}</span>
              <span className="font-semibold text-emerald-400">
                {formatCurrency(sub.mrr)}/mo
              </span>
            </div>
          </div>

          <ChevronRight className="h-5 w-5 text-gray-600 shrink-0" />
        </div>
      ))}
    </div>
  );
};
