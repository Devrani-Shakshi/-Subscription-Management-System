import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { StatusBadge } from '@/components/ui';
import type { AtRiskCustomer } from '@/types/company';

interface DashboardChurnPanelProps {
  customers: AtRiskCustomer[];
}

export const DashboardChurnPanel: React.FC<DashboardChurnPanelProps> = ({
  customers,
}) => {
  const navigate = useNavigate();

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-300">At-risk customers</h3>
        <Link
          to="/company/churn"
          className="text-xs text-violet-400 hover:text-violet-300 transition-colors flex items-center gap-1"
        >
          View all <ChevronRight className="h-3 w-3" />
        </Link>
      </div>

      {customers.length === 0 ? (
        <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-lg p-6 text-center">
          <p className="text-sm text-emerald-400 font-medium">No customers at risk</p>
          <p className="text-xs text-gray-500 mt-1">All customers are healthy</p>
        </div>
      ) : (
        <div className="divide-y divide-gray-800/50">
          {customers.slice(0, 5).map((c) => (
            <div
              key={c.id}
              className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"
            >
              <div className="h-8 w-8 rounded-full bg-gray-800 flex items-center justify-center
                              text-xs font-semibold text-gray-300 shrink-0">
                {c.name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 truncate">{c.name}</p>
              </div>
              <StatusBadge status={c.risk_level} />
              <button
                onClick={() => navigate(`/company/customers/${c.id}`)}
                className="text-xs text-gray-400 hover:text-violet-400 transition-colors
                           h-8 px-2 flex items-center rounded-lg hover:bg-violet-500/10"
              >
                View
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
