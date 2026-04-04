import React from 'react';
import { ChevronRight, Download, CreditCard } from 'lucide-react';
import { StatusBadge, Button } from '@/components/ui';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { PortalInvoice } from '@/types/portal';

interface RecentInvoicesCardProps {
  invoices: PortalInvoice[];
  onViewAll: () => void;
}

export const RecentInvoicesCard: React.FC<RecentInvoicesCardProps> = ({
  invoices,
  onViewAll,
}) => {
  if (invoices.length === 0) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">Recent Invoices</h3>
        <p className="text-sm text-gray-500">No invoices yet.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-200">Recent Invoices</h3>
        <button
          onClick={onViewAll}
          className="text-xs text-amber-400 hover:text-amber-300 transition-colors inline-flex items-center gap-1"
        >
          View all invoices
          <ChevronRight className="h-3 w-3" />
        </button>
      </div>

      <div className="divide-y divide-gray-800/50">
        {invoices.slice(0, 3).map((inv) => (
          <div
            key={inv.id}
            className="px-5 py-3.5 flex items-center justify-between gap-3"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className="min-w-0">
                <p className="text-sm text-gray-200 truncate">
                  {formatDate(inv.date)}
                </p>
                <p className="text-xs text-gray-500 font-mono">{inv.number}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <span className="text-sm font-medium text-gray-200">
                {formatCurrency(inv.amount)}
              </span>
              <StatusBadge status={inv.status} />

              {inv.status === 'overdue' ? (
                <Button variant="danger" size="sm" icon={<CreditCard className="h-3.5 w-3.5" />}>
                  Pay now
                </Button>
              ) : inv.status === 'paid' ? (
                <Button variant="ghost" size="sm" icon={<Download className="h-3.5 w-3.5" />}>
                  Download
                </Button>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
