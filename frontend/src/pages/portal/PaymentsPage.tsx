import React, { useState, useMemo } from 'react';
import { AlertTriangle, CreditCard, Wallet } from 'lucide-react';
import {
  PageHeader,
  PageLoader,
  PageError,
  PageEmpty,
  DataTable,
  StatusBadge,
  Button,
  MobileCard,
} from '@/components/ui';
import { useMyPayments, useMyInvoices } from '@/hooks/usePortal';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { formatCurrency, formatDate } from '@/lib/utils';
import { PortalPaymentModal } from './PortalPaymentModal';
import type { PortalPayment, PortalInvoice } from '@/types/portal';
import type { Column } from '@/types';

export const PaymentsPage: React.FC = () => {
  const { isMobile } = useBreakpoint();
  const { data: paymentsResp, isLoading, isError, refetch } = useMyPayments();
  const { data: invoiceData } = useMyInvoices({ status: 'overdue', page: 1, limit: 1 });
  const [payInvoice, setPayInvoice] = useState<PortalInvoice | null>(null);

  const overdueInvoice = invoiceData?.data?.[0] ?? null;
  const overdueTotal = useMemo(() => {
    return invoiceData?.data?.reduce((sum, inv) => sum + inv.amount, 0) ?? 0;
  }, [invoiceData]);

  const columns: Column<PortalPayment>[] = [
    {
      key: 'date',
      header: 'Date',
      render: (r) => formatDate(r.date),
      sortable: true,
    },
    {
      key: 'invoiceNumber',
      header: 'Invoice #',
      render: (r) => (
        <span className="font-mono text-xs text-gray-300">{r.invoiceNumber}</span>
      ),
    },
    {
      key: 'amount',
      header: 'Amount',
      render: (r) => (
        <span className="font-medium">{formatCurrency(r.amount)}</span>
      ),
      sortable: true,
    },
    {
      key: 'method',
      header: 'Method',
      render: (r) => (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-gray-800 text-gray-300 text-xs rounded-md capitalize">
          <Wallet className="h-3 w-3" />
          {r.method.replace('_', ' ')}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (r) => <StatusBadge status={r.status} />,
    },
  ];

  if (isLoading) return <PageLoader />;
  if (isError) return <PageError onRetry={refetch} />;

  const paymentList: PortalPayment[] = paymentsResp ?? [];

  return (
    <div className="space-y-6">
      <PageHeader title="Payment History" />

      {/* Overdue CTA */}
      {overdueInvoice && (
        <div className="rounded-xl border border-amber-500/30 bg-gradient-to-r from-amber-500/5 to-gray-900 p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-amber-500/10 flex items-center justify-center shrink-0">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-100">
                You have an outstanding balance of{' '}
                <span className="text-amber-400 font-bold">{formatCurrency(overdueTotal)}</span>
              </p>
              <p className="text-xs text-gray-400">
                Pay now to keep your subscription active.
              </p>
            </div>
          </div>
          <Button
            variant="amber"
            size="sm"
            onClick={() => setPayInvoice(overdueInvoice)}
            icon={<CreditCard className="h-4 w-4" />}
          >
            Pay overdue invoice
          </Button>
        </div>
      )}

      {/* Empty state */}
      {paymentList.length === 0 ? (
        <PageEmpty
          title="No payments yet"
          message="They'll appear here after your first payment."
        />
      ) : (
        <>
          {/* Desktop table */}
          <DataTable columns={columns} data={paymentList} />

          {/* Mobile cards */}
          {isMobile && (
            <div className="lg:hidden space-y-3">
              {paymentList.map((p) => (
                <MobileCard
                  key={p.id}
                  title={formatCurrency(p.amount)}
                  subtitle={formatDate(p.date)}
                  trailing={<StatusBadge status={p.status} />}
                  fields={[
                    { label: 'Invoice', value: p.invoiceNumber },
                    {
                      label: 'Method',
                      value: (
                        <span className="capitalize">{p.method.replace('_', ' ')}</span>
                      ),
                    },
                  ]}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Payment modal */}
      <PortalPaymentModal
        open={!!payInvoice}
        onClose={() => setPayInvoice(null)}
        invoice={payInvoice}
      />
    </div>
  );
};
