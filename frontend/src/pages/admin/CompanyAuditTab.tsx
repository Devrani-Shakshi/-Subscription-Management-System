import React, { useState } from 'react';
import { useAdminAudit } from '@/hooks/useAdmin';
import { DataTable, Pagination, PageLoader, PageEmpty, Button } from '@/components/ui';
import { formatDate } from '@/lib/utils';
import { AuditDiffModal } from './AuditDiffModal';
import type { AuditEntry, AuditFilters } from '@/types/admin';
import type { Column } from '@/types';

interface CompanyAuditTabProps {
  tenantId: string;
}

export const CompanyAuditTab: React.FC<CompanyAuditTabProps> = ({
  tenantId,
}) => {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [diffEntry, setDiffEntry] = useState<AuditEntry | null>(null);

  const filters: AuditFilters = {
    companyId: tenantId,
    entityType: '',
    action: '',
    actor: '',
    dateFrom: '',
    dateTo: '',
    page,
    limit,
  };

  const { data, isLoading } = useAdminAudit(filters);
  const entries = data?.data ?? [];
  const meta = data?.meta;

  const columns: Column<AuditEntry>[] = [
    { key: 'actor', header: 'Actor' },
    { key: 'actorRole', header: 'Role' },
    { key: 'entityType', header: 'Entity' },
    { key: 'action', header: 'Action' },
    { key: 'timestamp', header: 'Date', render: (row) => formatDate(row.timestamp) },
    {
      key: 'diff',
      header: '',
      width: '110px',
      render: (row) =>
        row.diff ? (
          <Button variant="ghost" size="sm" onClick={() => setDiffEntry(row)}>
            View changes
          </Button>
        ) : (
          <span className="text-xs text-gray-600">—</span>
        ),
    },
  ];

  if (isLoading) return <PageLoader />;
  if (entries.length === 0) return <PageEmpty title="No audit entries" message="No activity recorded yet." />;

  return (
    <div className="space-y-4">
      <DataTable columns={columns} data={entries} loading={isLoading} />

      {/* Mobile cards */}
      <div className="lg:hidden grid grid-cols-1 gap-3">
        {entries.map((e) => (
          <div key={e.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-medium text-gray-100">{e.actor}</p>
              <span className="text-xs text-gray-500">{formatDate(e.timestamp)}</span>
            </div>
            <p className="text-xs text-gray-400">
              {e.action} · {e.entityType} · {e.entityId}
            </p>
            {e.diff && (
              <Button variant="ghost" size="sm" onClick={() => setDiffEntry(e)} className="mt-2">
                View changes
              </Button>
            )}
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

      {diffEntry && (
        <AuditDiffModal
          entry={diffEntry}
          open={!!diffEntry}
          onClose={() => setDiffEntry(null)}
        />
      )}
    </div>
  );
};
