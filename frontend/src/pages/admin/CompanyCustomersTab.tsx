import React, { useState } from 'react';
import { useAdminCompanyCustomers } from '@/hooks/useAdmin';
import { DataTable, StatusBadge, Pagination, PageLoader, PageEmpty } from '@/components/ui';
import type { AdminCustomer } from '@/types/admin';
import type { Column } from '@/types';

interface CompanyCustomersTabProps {
  tenantId: string;
}

function churnBadgeVariant(score: number): 'success' | 'warning' | 'danger' {
  if (score >= 70) return 'danger';
  if (score >= 40) return 'warning';
  return 'success';
}

const columns: Column<AdminCustomer>[] = [
  { key: 'name', header: 'Name', sortable: true },
  { key: 'email', header: 'Email' },
  { key: 'subscriptionStatus', header: 'Sub Status', render: (row) => <StatusBadge status={row.subscriptionStatus} /> },
  { key: 'planName', header: 'Plan' },
  {
    key: 'churnScore',
    header: 'Churn Risk',
    sortable: true,
    render: (row) => (
      <StatusBadge
        status={`${row.churnScore}%`}
        variant={churnBadgeVariant(row.churnScore)}
      />
    ),
  },
];

export const CompanyCustomersTab: React.FC<CompanyCustomersTabProps> = ({
  tenantId,
}) => {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const { data, isLoading } = useAdminCompanyCustomers(tenantId, page, limit);

  const customers = data?.data ?? [];
  const meta = data?.meta;

  if (isLoading) return <PageLoader />;
  if (customers.length === 0) return <PageEmpty title="No customers" message="This company has no customers yet." />;

  return (
    <div className="space-y-4">
      <DataTable columns={columns} data={customers} loading={isLoading} />

      {/* Mobile cards */}
      <div className="lg:hidden grid grid-cols-1 gap-3">
        {customers.map((c) => (
          <div key={c.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-medium text-gray-100">{c.name}</p>
              <StatusBadge
                status={`${c.churnScore}%`}
                variant={churnBadgeVariant(c.churnScore)}
              />
            </div>
            <p className="text-xs text-gray-500">{c.email}</p>
            <div className="flex items-center gap-2 mt-2">
              <StatusBadge status={c.subscriptionStatus} />
              <span className="text-xs text-gray-500">· {c.planName}</span>
            </div>
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
