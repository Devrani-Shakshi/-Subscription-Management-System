import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { StatusBadge } from '@/components/ui';
import { formatDate } from '@/lib/utils';
import type { ActiveDunning } from '@/types/company';

interface DashboardDunningPanelProps {
  entries: ActiveDunning[];
}

export const DashboardDunningPanel: React.FC<DashboardDunningPanelProps> = ({
  entries,
}) => {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-300">Active dunning</h3>
        <Link
          to="/company/dunning"
          className="text-xs text-violet-400 hover:text-violet-300 transition-colors flex items-center gap-1"
        >
          View all <ChevronRight className="h-3 w-3" />
        </Link>
      </div>

      {entries.length === 0 ? (
        <div className="bg-gray-800/50 rounded-lg p-6 text-center">
          <p className="text-sm text-gray-400">No active dunning sequences</p>
        </div>
      ) : (
        <div className="divide-y divide-gray-800/50">
          {entries.slice(0, 5).map((d) => (
            <div key={d.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 truncate">
                  {d.invoice_number}
                  <span className="text-gray-500 ml-1.5">— {d.customer_name}</span>
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Attempt {d.attempt} · Next retry {formatDate(d.next_retry)}
                </p>
              </div>
              <StatusBadge status={d.status} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
