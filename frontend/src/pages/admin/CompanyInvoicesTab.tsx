import React, { useState } from 'react';
import { useAdminCompanyInvoices } from '@/hooks/useAdmin';
import { DataTable, StatusBadge, Pagination, PageLoader, PageEmpty } from '@/components/ui';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { AdminInvoice } from '@/types/admin';
import type { Column } from '@/types';

interface CompanyInvoicesTabProps {
  tenantId: string;
}

const columns: Column<AdminInvoice>[] = [
  { key: 'number', header: 'Invoice #', sortable: true },
  { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} /> },
  { key: 'total', header: 'Total', sortable: true, render: (row) => formatCurrency(row.total) },
  { key: 'dueDate', header: 'Due Date', render: (row) => formatDate(row.dueDate) },
];

export const CompanyInvoicesTab: React.FC<CompanyInvoicesTabProps> = ({
  tenantId,
}) => {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const { data, isLoading } = useAdminCompanyInvoices(tenantId, page, limit);

  const invoices = data?.data ?? [];
  const meta = data?.meta;

  if (isLoading) return <PageLoader />;
  if (invoices.length === 0) return <PageEmpty title="No invoices" message="This company has no invoices yet." />;

  return (
    <div className="space-y-4">
      <DataTable columns={columns} data={invoices} loading={isLoading} />

      {/* Mobile cards */}
      <div className="lg:hidden grid grid-cols-1 gap-3">
        {invoices.map((inv) => (
          <div key={inv.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-medium text-gray-100">{inv.number}</p>
              <StatusBadge status={inv.status} />
            </div>
            <div className="flex items-center justify-between mt-2">
              <span className="text-sm font-semibold text-gray-200">{formatCurrency(inv.total)}</span>
              <span className="text-xs text-gray-500">Due {formatDate(inv.dueDate)}</span>
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
