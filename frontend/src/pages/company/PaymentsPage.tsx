import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import {
  PageHeader, FilterBar, DataTable, Pagination,
  StatusBadge, StatCard, Button, PageLoader, PageError,
} from '@/components/ui';
import { usePayments, usePaymentSummary } from '@/hooks/usePayments';
import { formatCurrency, formatDate } from '@/lib/utils';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import type { Column, FilterConfig } from '@/types';
import type { Payment, PaymentFilters } from '@/types/billing';
import { RecordPaymentModal } from './payments/RecordPaymentModal';

const FILTERS: FilterConfig[] = [
  { key: 'method', label: 'Method', type: 'select', options: [
    { label: 'Credit card', value: 'credit_card' },
    { label: 'Bank transfer', value: 'bank_transfer' },
    { label: 'Cash', value: 'cash' },
    { label: 'Check', value: 'check' },
  ]},
  { key: 'customer', label: 'Customer', type: 'search' },
  { key: 'dateFrom', label: 'From', type: 'date' },
  { key: 'dateTo', label: 'To', type: 'date' },
];

export const PaymentsPage: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();
  const [modalOpen, setModalOpen] = useState(false);
  const [filters, setFilters] = useState<PaymentFilters>({ page: 1, limit: 10 });
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});

  const { data, isLoading, isError, refetch } = usePayments(filters);
  const { data: summaryRes } = usePaymentSummary();
  const summary = summaryRes?.data;

  const payments = data?.data ?? [];
  const meta = data?.meta;

  const handleFilterChange = (key: string, value: string) => {
    setFilterValues((prev) => ({ ...prev, [key]: value }));
    setFilters((prev) => ({ ...prev, [key]: value || undefined, page: 1 }));
  };

  const columns: Column<Payment>[] = [
    { key: 'invoiceNumber', header: 'Invoice #', sortable: true, render: (r) => (
      <span className="font-mono text-gray-200">{r.invoiceNumber}</span>
    )},
    { key: 'customerName', header: 'Customer', sortable: true },
    { key: 'amount', header: 'Amount', sortable: true, render: (r) => (
      <span className="font-semibold text-gray-100">{formatCurrency(r.amount)}</span>
    )},
    { key: 'method', header: 'Method', render: (r) => (
      <StatusBadge status={r.method.replace('_', ' ')} variant="info" />
    )},
    { key: 'date', header: 'Date', sortable: true, render: (r) => formatDate(r.date) },
    { key: 'actions', header: '', render: (r) => (
      <Button variant="ghost" size="sm"
        onClick={(e) => { e.stopPropagation(); navigate(`/company/invoices/${r.invoiceId}`); }}>
        View invoice
      </Button>
    )},
  ];

  if (isLoading) return <PageLoader />;
  if (isError) return <PageError onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payments"
        subtitle="Track received payments and outstanding balances"
        actions={
          <Button icon={<Plus className="h-4 w-4" />} onClick={() => setModalOpen(true)}>
            Record payment
          </Button>
        }
      />

      {/* Summary strip */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="Total received" value={formatCurrency(summary.totalReceived)}
            icon="DollarSign" color="teal" />
          <StatCard label="Outstanding" value={formatCurrency(summary.outstanding)}
            icon="Clock" color="amber" />
          <StatCard label="Overdue" value={formatCurrency(summary.overdue)}
            icon="AlertTriangle" color="rose" />
        </div>
      )}

      <FilterBar filters={FILTERS} values={filterValues} onChange={handleFilterChange} />

      {/* Desktop */}
      <DataTable columns={columns} data={payments} loading={isLoading}
        empty="No payments found" onRowClick={(r) => navigate(`/company/invoices/${r.invoiceId}`)} />

      {/* Mobile cards */}
      {isMobile && (
        <div className="lg:hidden space-y-3">
          {payments.map((p) => (
            <div key={p.id}
              onClick={() => navigate(`/company/invoices/${p.invoiceId}`)}
              className="bg-gray-900 border border-gray-800 rounded-xl p-4 cursor-pointer hover:border-gray-600 transition-all">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="text-lg font-bold text-gray-50">{formatCurrency(p.amount)}</p>
                  <p className="text-sm text-gray-400">{p.customerName}</p>
                </div>
                <StatusBadge status={p.method.replace('_', ' ')} variant="info" />
              </div>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span className="font-mono">{p.invoiceNumber}</span>
                <span>{formatDate(p.date)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {meta && (
        <Pagination
          total={meta.total} page={meta.page} limit={meta.limit}
          onPageChange={(p) => setFilters((prev) => ({ ...prev, page: p }))}
          onLimitChange={(l) => setFilters((prev) => ({ ...prev, limit: l, page: 1 }))}
        />
      )}

      <RecordPaymentModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
};
