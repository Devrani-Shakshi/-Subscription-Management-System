import React from 'react';
import { useNavigate } from 'react-router-dom';
import { StatusBadge, Button } from '@/components/ui';
import { formatCurrency, formatDate } from '@/lib/utils';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import type { Invoice } from '@/types/billing';

interface InvoiceMobileListProps {
  invoices: Invoice[];
  onConfirm: (id: string) => void;
  onDownload: (id: string) => void;
  confirmLoading: boolean;
  downloadLoading: boolean;
}

function getActionLabel(status: string): string {
  switch (status) {
    case 'draft':
      return 'Confirm';
    case 'confirmed':
    case 'overdue':
      return 'Pay';
    case 'paid':
      return 'Download';
    default:
      return 'View';
  }
}

export const InvoiceMobileList: React.FC<InvoiceMobileListProps> = ({
  invoices,
  onConfirm,
  onDownload,
  confirmLoading,
  downloadLoading,
}) => {
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();

  if (!isMobile) return null;

  return (
    <div className="lg:hidden space-y-3">
      {invoices.map((inv) => {
        const isOverdue = inv.status === 'overdue';
        return (
          <div
            key={inv.id}
            onClick={() => navigate(`/company/invoices/${inv.id}`)}
            className={`
              bg-gray-900 border rounded-xl p-4 cursor-pointer
              hover:border-gray-600 transition-all duration-200
              ${isOverdue ? 'border-l-4 border-l-red-500 border-gray-800' : 'border-gray-800'}
            `.trim()}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <span className="font-mono text-sm font-semibold text-gray-100">
                  {inv.number}
                </span>
                <p className="text-sm text-gray-400 mt-0.5">{inv.customerName}</p>
              </div>
              <StatusBadge status={inv.status} />
            </div>

            <div className="flex items-end justify-between">
              <div>
                <p className="text-lg font-bold text-gray-50">
                  {formatCurrency(inv.total)}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Due {formatDate(inv.dueDate)}
                </p>
              </div>
              <Button
                variant={inv.status === 'draft' ? 'primary' : 'secondary'}
                size="sm"
                loading={
                  inv.status === 'draft'
                    ? confirmLoading
                    : inv.status === 'paid'
                    ? downloadLoading
                    : false
                }
                onClick={(e) => {
                  e.stopPropagation();
                  if (inv.status === 'draft') onConfirm(inv.id);
                  else if (inv.status === 'paid') onDownload(inv.id);
                  else navigate(`/company/invoices/${inv.id}`);
                }}
              >
                {getActionLabel(inv.status)}
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );
};
