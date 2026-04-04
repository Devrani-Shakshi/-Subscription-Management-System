import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, ExternalLink } from 'lucide-react';
import { StatusBadge } from '@/components/ui';
import { useSubscriptionInvoices } from '@/hooks/useSubscriptions';
import { formatCurrency, formatDate } from '@/lib/utils';

interface InvoiceHistoryTableProps {
  subscriptionId: string;
}

export const InvoiceHistoryTable: React.FC<InvoiceHistoryTableProps> = ({
  subscriptionId,
}) => {
  const navigate = useNavigate();
  const { data: invoices, isLoading } = useSubscriptionInvoices(subscriptionId);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-800 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          Recent Invoices
        </h3>
        <button
          onClick={() => navigate('/company/invoices')}
          className="text-xs text-violet-400 hover:text-violet-300 transition-colors
                     flex items-center gap-1"
        >
          View all <ExternalLink className="h-3 w-3" />
        </button>
      </div>

      {isLoading ? (
        <div className="p-4 space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-10 bg-gray-800 rounded animate-pulse" />
          ))}
        </div>
      ) : !invoices || invoices.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <FileText className="h-8 w-8 text-gray-700 mb-2" />
          <p className="text-sm text-gray-500">No invoices yet</p>
        </div>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-xs font-semibold text-gray-500 uppercase">
              <th className="px-5 py-2 text-left">Invoice</th>
              <th className="px-3 py-2 text-left">Status</th>
              <th className="px-3 py-2 text-right">Amount</th>
              <th className="px-5 py-2 text-right">Due</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv) => (
              <tr
                key={inv.id}
                className="border-b border-gray-800/30 last:border-0
                           hover:bg-gray-800/30 cursor-pointer transition-colors"
                onClick={() => navigate(`/company/invoices/${inv.id}`)}
              >
                <td className="px-5 py-2.5 font-mono text-xs text-gray-300">
                  {inv.number}
                </td>
                <td className="px-3 py-2.5">
                  <StatusBadge status={inv.status} />
                </td>
                <td className="px-3 py-2.5 text-right text-gray-200">
                  {formatCurrency(inv.amount)}
                </td>
                <td className="px-5 py-2.5 text-right text-gray-500 text-xs">
                  {formatDate(inv.dueDate)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
