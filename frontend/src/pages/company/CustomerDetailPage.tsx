import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, ChevronDown, ChevronUp } from 'lucide-react';
import { useCustomerDetail } from '@/hooks/useCustomers';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Column } from '@/types';
import type { CustomerInvoice, DunningEntry } from '@/types/company';
import {
  PageHeader, PageLoader, PageError, StatusBadge, DataTable, MobileCard,
} from '@/components/ui';
import { useBreakpoint } from '@/hooks/useBreakpoint';

/* ── Churn gauge SVG ──────────────────────────────────────── */
const ChurnGauge: React.FC<{ score: number }> = ({ score }) => {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const color =
    score >= 70 ? '#ef4444' : score >= 30 ? '#f59e0b' : '#34d399';

  return (
    <div className="flex flex-col items-center">
      <svg width="100" height="100" viewBox="0 0 100 100" className="-rotate-90">
        <circle cx="50" cy="50" r={radius} fill="none" stroke="#1f2937" strokeWidth="8" />
        <circle cx="50" cy="50" r={radius} fill="none" stroke={color}
          strokeWidth="8" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={circumference - progress}
          className="transition-all duration-700"
        />
      </svg>
      <span className="text-2xl font-bold text-gray-100 -mt-16">{score}%</span>
      <span className="text-xs text-gray-500 mt-1">Churn risk</span>
    </div>
  );
};

export const CustomerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: customer, isLoading, error } = useCustomerDetail(id!);
  const { isMobile } = useBreakpoint();
  const [dunningOpen, setDunningOpen] = useState(false);

  if (isLoading) return <PageLoader />;
  if (error || !customer) {
    return <PageError message="Customer not found" onRetry={() => window.location.reload()} />;
  }

  const invoiceColumns: Column<CustomerInvoice>[] = [
    { key: 'invoice_number', header: 'Invoice #', sortable: true },
    {
      key: 'status', header: 'Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: 'total', header: 'Total',
      render: (row) => formatCurrency(row.total),
    },
    {
      key: 'due_date', header: 'Due Date',
      render: (row) => formatDate(row.due_date),
    },
    {
      key: 'paid_at', header: 'Paid',
      render: (row) => (row.paid_at ? formatDate(row.paid_at) : '—'),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={customer.name}
        subtitle={customer.email}
        breadcrumbs={[
          { label: 'Customers', href: '/company/customers' },
          { label: customer.name },
        ]}
        actions={
          <Link
            to="/company/customers"
            className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-200 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" /> Back
          </Link>
        }
      />

      {/* 3-col grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Subscription card */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
          <h3 className="text-sm font-semibold text-gray-300">Subscription</h3>
          {customer.subscription ? (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Plan</span>
                <span className="text-gray-100 font-medium">{customer.subscription.plan_name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Status</span>
                <StatusBadge status={customer.subscription.status} />
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Started</span>
                <span className="text-gray-200">{formatDate(customer.subscription.start_date)}</span>
              </div>
              {customer.subscription.expiry_date && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Expires</span>
                  <span className="text-gray-200">{formatDate(customer.subscription.expiry_date)}</span>
                </div>
              )}
              <div className="pt-2 border-t border-gray-800">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">MRR Contribution</span>
                  <span className="text-teal-400 font-semibold">
                    {formatCurrency(customer.subscription.mrr)}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">No active subscription</p>
          )}
        </div>

        {/* Churn card */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-gray-300">Churn Analysis</h3>
          {customer.churn ? (
            <>
              <ChurnGauge score={customer.churn.score} />
              <ul className="space-y-2 mt-2">
                {customer.churn.signals.map((sig, i) => (
                  <li key={i} className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">{sig.label}</span>
                    <span className={
                      sig.impact === 'negative' ? 'text-red-400' :
                      sig.impact === 'positive' ? 'text-emerald-400' : 'text-gray-500'
                    }>
                      {sig.value}
                    </span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm text-gray-500">No churn data</p>
          )}
        </div>

        {/* Billing card — last 3 invoices */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
          <h3 className="text-sm font-semibold text-gray-300">Recent Invoices</h3>
          {customer.recent_invoices.length > 0 ? (
            <ul className="divide-y divide-gray-800">
              {customer.recent_invoices.slice(0, 3).map((inv) => (
                <li key={inv.id} className="flex items-center justify-between py-2.5">
                  <div>
                    <p className="text-sm text-gray-200 font-medium">{inv.invoice_number}</p>
                    <p className="text-xs text-gray-500">{formatDate(inv.due_date)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-200">{formatCurrency(inv.total)}</p>
                    <StatusBadge status={inv.status} className="mt-0.5" />
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">No invoices yet</p>
          )}
        </div>
      </div>

      {/* Full invoice history */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Invoice History</h3>
        <DataTable
          columns={invoiceColumns}
          data={customer.invoices}
          empty="No invoices for this customer"
        />
        {isMobile && customer.invoices.length > 0 && (
          <div className="space-y-3 lg:hidden">
            {customer.invoices.map((inv) => (
              <MobileCard
                key={inv.id}
                title={inv.invoice_number}
                subtitle={formatDate(inv.due_date)}
                fields={[
                  { label: 'Total', value: formatCurrency(inv.total) },
                  { label: 'Status', value: <StatusBadge status={inv.status} /> },
                ]}
              />
            ))}
          </div>
        )}
      </div>

      {/* Dunning history — collapsible */}
      {customer.dunning_history.length > 0 && (
        <div className="border border-gray-800 rounded-xl overflow-hidden">
          <button
            onClick={() => setDunningOpen(!dunningOpen)}
            className="w-full flex items-center justify-between px-5 py-3
                       text-sm font-semibold text-gray-300 hover:bg-gray-800/40 transition-colors"
          >
            Dunning History ({customer.dunning_history.length})
            {dunningOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
          {dunningOpen && (
            <div className="px-5 pb-4 space-y-2 animate-fade-in">
              {customer.dunning_history.map((entry) => (
                <div key={entry.id} className="flex items-start gap-3 text-sm py-2 border-t border-gray-800/50">
                  <StatusBadge status={entry.status} />
                  <div className="flex-1 min-w-0">
                    <p className="text-gray-200">{entry.type}</p>
                    <p className="text-gray-500 text-xs">{entry.message}</p>
                  </div>
                  <span className="text-xs text-gray-500 shrink-0">{formatDate(entry.sent_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
