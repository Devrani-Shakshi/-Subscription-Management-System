import React, { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import {
  PageHeader, FilterBar, DataTable, Pagination,
  StatusBadge, StatCard, PageLoader, PageError,
} from '@/components/ui';
import { useDunningSchedules, useDunningSummary } from '@/hooks/useDunning';
import { formatDate } from '@/lib/utils';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import type { Column, FilterConfig } from '@/types';
import type { DunningSchedule, DunningFilters } from '@/types/billing';

const FILTERS: FilterConfig[] = [
  { key: 'status', label: 'Status', type: 'select', options: [
    { label: 'Pending', value: 'pending' },
    { label: 'Success', value: 'success' },
    { label: 'Failed', value: 'failed' },
    { label: 'Skipped', value: 'skipped' },
  ]},
  { key: 'dateFrom', label: 'From', type: 'date' },
  { key: 'dateTo', label: 'To', type: 'date' },
];

export const DunningPage: React.FC = () => {
  const { isMobile } = useBreakpoint();
  const [filters, setFilters] = useState<DunningFilters>({ page: 1, limit: 10 });
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const { data, isLoading, isError, refetch } = useDunningSchedules(filters);
  const { data: summaryRes } = useDunningSummary();
  const summary = summaryRes?.data;

  const schedules = data?.data ?? [];
  const meta = data?.meta;

  const handleFilterChange = (key: string, value: string) => {
    setFilterValues((prev) => ({ ...prev, [key]: value }));
    setFilters((prev) => ({ ...prev, [key]: value || undefined, page: 1 }));
  };

  const columns: Column<DunningSchedule>[] = [
    { key: 'invoiceNumber', header: 'Invoice #', sortable: true, render: (r) => (
      <span className="font-mono text-gray-200">{r.invoiceNumber}</span>
    )},
    { key: 'customerName', header: 'Customer', sortable: true },
    { key: 'attempt', header: 'Attempt #', render: (r) => (
      <span className="font-mono text-gray-300">#{r.attempt}</span>
    )},
    { key: 'scheduledDate', header: 'Scheduled', sortable: true, render: (r) => formatDate(r.scheduledDate) },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'result', header: 'Result', render: (r) => (
      <span className="text-sm text-gray-400 truncate max-w-[200px] inline-block">
        {r.result || '—'}
      </span>
    )},
    { key: 'nextRetryDate', header: 'Next retry', render: (r) => (
      r.nextRetryDate ? formatDate(r.nextRetryDate) : <span className="text-gray-600">—</span>
    )},
  ];

  if (isLoading) return <PageLoader />;
  if (isError) return <PageError onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dunning engine"
        subtitle="Automated payment retry sequences and collection management"
      />

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="Active sequences" value={summary.activeSequences}
            icon="RefreshCw" color="violet" />
          <StatCard label="Retries today" value={summary.retriesToday}
            icon="Repeat" color="teal" />
          <StatCard label="Suspended this month" value={summary.suspendedThisMonth}
            icon="PauseCircle" color="rose" />
        </div>
      )}

      <FilterBar filters={FILTERS} values={filterValues} onChange={handleFilterChange} />

      {/* Desktop table with expandable rows */}
      <div className="hidden lg:block overflow-x-auto rounded-xl border border-gray-800 bg-gray-900/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="w-8 px-2" />
              {columns.map((col) => (
                <th key={col.key} className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {schedules.map((row) => (
              <React.Fragment key={row.id}>
                <tr className="border-b border-gray-800/30 hover:bg-gray-800/40 transition-colors cursor-pointer"
                  onClick={() => setExpandedRow(expandedRow === row.id ? null : row.id)}>
                  <td className="px-2">
                    {expandedRow === row.id
                      ? <ChevronDown className="h-4 w-4 text-gray-500" />
                      : <ChevronRight className="h-4 w-4 text-gray-500" />}
                  </td>
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 text-gray-200">
                      {col.render ? col.render(row) : (row[col.key as keyof DunningSchedule] as React.ReactNode) ?? '—'}
                    </td>
                  ))}
                </tr>
                {expandedRow === row.id && (
                  <tr className="bg-gray-800/20">
                    <td colSpan={columns.length + 1} className="px-6 py-4">
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Result details</p>
                      <pre className="text-xs text-gray-400 bg-gray-800 rounded-lg p-3 overflow-x-auto font-mono">
                        {JSON.stringify(row.resultJson, null, 2)}
                      </pre>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      {isMobile && (
        <div className="lg:hidden space-y-3">
          {schedules.map((s) => (
            <div key={s.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="text-sm font-medium text-gray-200">{s.customerName}</p>
                  <p className="font-mono text-xs text-gray-500">{s.invoiceNumber}</p>
                </div>
                <StatusBadge status={s.status} />
              </div>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>Attempt #{s.attempt}</span>
                <span>{s.nextRetryDate ? `Next: ${formatDate(s.nextRetryDate)}` : 'No retry'}</span>
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
    </div>
  );
};
