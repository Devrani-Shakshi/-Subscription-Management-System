import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Send, Download, CheckCircle, XCircle } from 'lucide-react';
import {
  PageHeader, FilterBar, DataTable, Pagination,
  StatusBadge, Button, PageLoader, PageError,
} from '@/components/ui';
import { useInvoices, useConfirmInvoice, useSendInvoice, useDownloadInvoicePdf, useCancelInvoice } from '@/hooks/useInvoices';
import { formatCurrency, formatDate } from '@/lib/utils';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import type { Column, FilterConfig } from '@/types';
import type { Invoice, InvoiceFilters } from '@/types/billing';
import { InvoiceMobileList } from './invoices/InvoiceMobileList';
import { GenerateInvoiceModal } from './invoices/GenerateInvoiceModal';

const FILTERS: FilterConfig[] = [
  { key: 'status', label: 'Status', type: 'select', options: [
    { label: 'Draft', value: 'draft' }, { label: 'Confirmed', value: 'confirmed' },
    { label: 'Paid', value: 'paid' }, { label: 'Overdue', value: 'overdue' },
    { label: 'Cancelled', value: 'cancelled' },
  ]},
  { key: 'customer', label: 'Customer', type: 'search' },
  { key: 'dateFrom', label: 'From', type: 'date' },
  { key: 'dateTo', label: 'To', type: 'date' },
];

export const InvoicesPage: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();
  const [modalOpen, setModalOpen] = useState(false);
  const [filters, setFilters] = useState<InvoiceFilters>({ page: 1, limit: 10 });
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});

  const { data, isLoading, isError, refetch } = useInvoices(filters);
  const confirm = useConfirmInvoice();
  const send = useSendInvoice();
  const download = useDownloadInvoicePdf();
  const cancel = useCancelInvoice();

  const invoices = data?.data ?? [];
  const meta = data?.meta;

  const handleFilterChange = (key: string, value: string) => {
    setFilterValues((prev) => ({ ...prev, [key]: value }));
    setFilters((prev) => ({ ...prev, [key]: value || undefined, page: 1 }));
  };

  const columns: Column<Invoice>[] = [
    { key: 'number', header: 'Invoice #', sortable: true, render: (r) => (
      <span className="font-mono font-semibold text-gray-100">{r.number}</span>
    )},
    { key: 'customerName', header: 'Customer', sortable: true },
    { key: 'subscriptionName', header: 'Subscription' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'dueDate', header: 'Due date', sortable: true, render: (r) => formatDate(r.dueDate) },
    { key: 'total', header: 'Total', sortable: true, render: (r) => (
      <span className="font-semibold">{formatCurrency(r.total)}</span>
    )},
    { key: 'actions', header: 'Actions', render: (r) => (
      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
        {r.status === 'draft' && (
          <Button variant="ghost" size="sm" icon={<CheckCircle className="h-4 w-4" />}
            loading={confirm.isPending} onClick={() => confirm.mutate(r.id)}>Confirm</Button>
        )}
        {(r.status === 'confirmed' || r.status === 'overdue') && (
          <Button variant="ghost" size="sm" icon={<Send className="h-4 w-4" />}
            loading={send.isPending} onClick={() => send.mutate(r.id)}>Send</Button>
        )}
        <Button variant="ghost" size="sm" icon={<Download className="h-4 w-4" />}
          loading={download.isPending} onClick={() => download.mutate(r.id)}>PDF</Button>
        {r.status !== 'cancelled' && r.status !== 'paid' && (
          <Button variant="ghost" size="sm" icon={<XCircle className="h-4 w-4 text-red-400" />}
            loading={cancel.isPending} onClick={() => cancel.mutate(r.id)}>Cancel</Button>
        )}
      </div>
    )},
  ];

  if (isLoading) return <PageLoader />;
  if (isError) return <PageError onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Invoices"
        subtitle="Manage and track all company invoices"
        actions={
          <Button icon={<Plus className="h-4 w-4" />} onClick={() => setModalOpen(true)}>
            Generate invoice
          </Button>
        }
      />

      <FilterBar filters={FILTERS} values={filterValues} onChange={handleFilterChange} />

      {/* Desktop table — overdue rows have red left border */}
      <div className="hidden lg:block">
        <div className="overflow-x-auto rounded-xl border border-gray-800 bg-gray-900/50">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                {columns.map((col) => (
                  <th key={col.key} className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    {col.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id}
                  onClick={() => navigate(`/company/invoices/${inv.id}`)}
                  className={`
                    border-b border-gray-800/30 last:border-0 cursor-pointer
                    hover:bg-gray-800/40 transition-colors duration-150
                    ${inv.status === 'overdue' ? 'border-l-4 border-l-red-500' : ''}
                  `.trim()}>
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 text-gray-200">
                      {col.render ? col.render(inv) : (inv[col.key as keyof Invoice] as React.ReactNode) ?? '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile */}
      {isMobile && (
        <InvoiceMobileList
          invoices={invoices}
          onConfirm={(id) => confirm.mutate(id)}
          onDownload={(id) => download.mutate(id)}
          confirmLoading={confirm.isPending}
          downloadLoading={download.isPending}
        />
      )}

      {meta && (
        <Pagination
          total={meta.total} page={meta.page} limit={meta.limit}
          onPageChange={(p) => setFilters((prev) => ({ ...prev, page: p }))}
          onLimitChange={(l) => setFilters((prev) => ({ ...prev, limit: l, page: 1 }))}
        />
      )}

      <GenerateInvoiceModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
};
