import React, { useState } from 'react';
import { useAdminCompanySubscriptions } from '@/hooks/useAdmin';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { DataTable, StatusBadge, Pagination, PageLoader, PageEmpty } from '@/components/ui';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { AdminSubscription } from '@/types/admin';
import type { Column } from '@/types';

interface CompanySubscriptionsTabProps {
  tenantId: string;
}

const columns: Column<AdminSubscription>[] = [
  { key: 'customerName', header: 'Customer', sortable: true },
  { key: 'planName', header: 'Plan' },
  { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} /> },
  { key: 'mrr', header: 'MRR', sortable: true, render: (row) => formatCurrency(row.mrr) },
  { key: 'startDate', header: 'Start', render: (row) => formatDate(row.startDate) },
  { key: 'endDate', header: 'End', render: (row) => (row.endDate ? formatDate(row.endDate) : '—') },
];

export const CompanySubscriptionsTab: React.FC<CompanySubscriptionsTabProps> = ({
  tenantId,
}) => {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const { data, isLoading } = useAdminCompanySubscriptions(tenantId, page, limit);
  const { isMobile } = useBreakpoint();

  const subs = data?.data ?? [];
  const meta = data?.meta;

  if (isLoading) return <PageLoader />;
  if (subs.length === 0) return <PageEmpty title="No subscriptions" message="This company has no subscriptions yet." />;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded-full">
          View only
        </span>
      </div>

      <DataTable columns={columns} data={subs} loading={isLoading} />

      {/* Mobile cards */}
      <div className="lg:hidden grid grid-cols-1 gap-3">
        {subs.map((s) => (
          <div key={s.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-100">{s.customerName}</p>
              <StatusBadge status={s.status} />
            </div>
            <p className="text-xs text-gray-500">{s.planName}</p>
            <p className="text-sm font-semibold text-gray-200 mt-2">{formatCurrency(s.mrr)}/mo</p>
          </div>
        ))}
      </div>

      {meta && (
        <Pagination
          total={meta.total}
          page={page}
          limit={limit}
          onPageChange={setPage}
          onLimitChange={(l) => { setLimit(l); setPage(1); }}
        />
      )}
    </div>
  );
};
