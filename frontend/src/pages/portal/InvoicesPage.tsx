import React, { useState, useMemo } from 'react';
import { AlertTriangle, CreditCard, Download, FileText } from 'lucide-react';
import {
  PageHeader,
  PageLoader,
  PageError,
  PageEmpty,
  DataTable,
  FilterBar,
  StatusBadge,
  Button,
  MobileCard,
  Pagination,
} from '@/components/ui';
import { useMyInvoices, useDownloadPortalInvoicePdf } from '@/hooks/usePortal';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { formatCurrency, formatDate } from '@/lib/utils';
import { PortalPaymentModal } from './PortalPaymentModal';
import type { PortalInvoice, PortalInvoiceFilters } from '@/types/portal';
import type { Column, FilterConfig } from '@/types';

const STATUS_FILTERS: FilterConfig[] = [
  {
    key: 'status',
    label: 'Status',
    type: 'select',
    options: [
      { label: 'Paid', value: 'paid' },
      { label: 'Overdue', value: 'overdue' },
      { label: 'Pending', value: 'pending' },
    ],
  },
  { key: 'dateFrom', label: 'From', type: 'date' },
  { key: 'dateTo', label: 'To', type: 'date' },
];

export const InvoicesPage: React.FC = () => {
  const { isMobile } = useBreakpoint();
  const [filters, setFilters] = useState<PortalInvoiceFilters>({ page: 1, limit: 10 });
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [payInvoice, setPayInvoice] = useState<PortalInvoice | null>(null);
  
  const download = useDownloadPortalInvoicePdf();

  const { data, isLoading, isError, refetch } = useMyInvoices({
    ...filters,
    status: filterValues.status || undefined,
    dateFrom: filterValues.dateFrom || undefined,
    dateTo: filterValues.dateTo || undefined,
  });

  const invoices = data?.data ?? [];
  const meta = data?.meta;

  const overdueInvoices = useMemo(
    () => invoices.filter((i) => i.status === 'overdue'),
    [invoices]
  );
  const overdueTotal = useMemo(
    () => overdueInvoices.reduce((sum, i) => sum + i.amount, 0),
    [overdueInvoices]
  );

  const handleFilterChange = (key: string, value: string) => {
    setFilterValues((prev) => ({ ...prev, [key]: value }));
    setFilters((prev) => ({ ...prev, page: 1 }));
  };

  const columns: Column<PortalInvoice>[] = [
    { key: 'number', header: 'Invoice #', render: (r) => (
      <span className="font-mono text-gray-300 text-xs">{r.number}</span>
    )},
    { key: 'date', header: 'Date', render: (r) => formatDate(r.date), sortable: true },
    { key: 'dueDate', header: 'Due Date', render: (r) => formatDate(r.dueDate), sortable: true },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'amount', header: 'Total', render: (r) => (
      <span className="font-medium">{formatCurrency(r.amount)}</span>
    ), sortable: true },
    {
      key: 'actions',
      header: 'Actions',
      render: (r) => {
        const canPay = ['overdue', 'confirmed', 'draft', 'pending'].includes(r.status);
        const canDownload = r.status === 'paid';

        if (canPay) {
          return (
            <Button variant="danger" size="sm" onClick={() => setPayInvoice(r)}
              icon={<CreditCard className="h-3.5 w-3.5" />}>
              Pay now
            </Button>
          );
        }
        if (canDownload) {
          return (
            <Button variant="ghost" size="sm" icon={<Download className="h-3.5 w-3.5" />} loading={download.isPending} onClick={() => download.mutate(r.id)}>
              Download
            </Button>
          );
        }
        return null;
      },
    },
  ];

  if (isLoading) return <PageLoader />;
  if (isError) return <PageError onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader title="My Invoices" />

      {/* Overdue banner */}
      {overdueInvoices.length > 0 && (
        <div className="rounded-xl border border-red-500/30 bg-gradient-to-r from-red-500/5 to-amber-500/5 p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-red-500/10 flex items-center justify-center shrink-0">
              <AlertTriangle className="h-5 w-5 text-red-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-100">
                You have {overdueInvoices.length} overdue invoice{overdueInvoices.length > 1 ? 's' : ''}
              </p>
              <p className="text-xs text-gray-400">
                Total due: <span className="text-red-400 font-semibold">{formatCurrency(overdueTotal)}</span>
              </p>
            </div>
          </div>
          <Button
            variant="danger"
            size="sm"
            onClick={() => setPayInvoice(overdueInvoices[0])}
            icon={<CreditCard className="h-4 w-4" />}
          >
            Pay now
          </Button>
        </div>
      )}

      {/* Filters */}
      <FilterBar
        filters={STATUS_FILTERS}
        values={filterValues}
        onChange={handleFilterChange}
      />

      {/* Empty state */}
      {invoices.length === 0 ? (
        <PageEmpty
          title="No invoices"
          message="Your invoices will appear here once generated."
        />
      ) : (
        <>
          {/* Desktop table */}
          <DataTable columns={columns} data={invoices} />

          {/* Mobile cards */}
          {isMobile && (
            <div className="lg:hidden space-y-3">
              {invoices.map((inv) => (
                <InvoiceMobileCard
                  key={inv.id}
                  invoice={inv}
                  onPay={() => setPayInvoice(inv)}
                  onDownload={() => download.mutate(inv.id)}
                  isDownloading={download.isPending}
                />
              ))}
            </div>
          )}

          {/* Pagination */}
          {meta && (
            <Pagination
              page={filters.page ?? 1}
              total={meta.total}
              limit={meta.limit}
              onPageChange={(p: number) => setFilters((prev) => ({ ...prev, page: p }))}
              onLimitChange={(l: number) => setFilters((prev) => ({ ...prev, limit: l, page: 1 }))}
            />
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

/* ── Invoice Mobile Card ─────────────────────────── */

interface InvoiceMobileCardProps {
  invoice: PortalInvoice;
  onPay: () => void;
  onDownload: () => void;
  isDownloading: boolean;
}

const InvoiceMobileCard: React.FC<InvoiceMobileCardProps> = ({ invoice, onPay, onDownload, isDownloading }) => {
  const isOverdue = invoice.status === 'overdue';
  const isPaid = invoice.status === 'paid';
  const canPay = ['overdue', 'confirmed', 'draft', 'pending'].includes(invoice.status);

  return (
    <div
      className={`
        bg-gray-900 border rounded-xl p-4 transition-colors
        ${isOverdue ? 'border-l-red-500 border-l-2 border-gray-800' : 'border-gray-800'}
      `.trim()}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <p className="text-xs text-gray-500 font-mono">{invoice.number}</p>
          <p className="text-sm text-gray-400 mt-0.5">
            Due {formatDate(invoice.dueDate)}
          </p>
        </div>
        <StatusBadge status={invoice.status} className="text-sm px-3 py-1" />
      </div>

      <div className="flex items-end justify-between">
        <p className="text-xl font-bold text-gray-100">{formatCurrency(invoice.amount)}</p>

        {canPay && (
          <Button variant="danger" size="sm" className="w-full mt-3" onClick={onPay}>
            <CreditCard className="h-4 w-4 mr-1" />
            Pay Now
          </Button>
        )}
        {isPaid && (
          <Button variant="ghost" size="sm" icon={<Download className="h-4 w-4" />} loading={isDownloading} onClick={onDownload}>
            Download PDF
          </Button>
        )}
      </div>
    </div>
  );
};
