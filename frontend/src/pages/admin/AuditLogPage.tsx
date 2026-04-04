import React, { useState, useCallback } from 'react';
import { Download } from 'lucide-react';
import { useAdminAudit } from '@/hooks/useAdmin';
import { api } from '@/lib/axios';
import { PageHeader, DataTable, FilterBar, Pagination, Button, PageLoader, PageError } from '@/components/ui';
import { formatDate } from '@/lib/utils';
import { AuditDiffModal } from './AuditDiffModal';
import { AUDIT_FILTER_CONFIGS, getAuditColumns } from './AuditColumns';
import type { AuditEntry, AuditFilters } from '@/types/admin';

export const AuditLogPage: React.FC = () => {
  const [filters, setFilters] = useState<AuditFilters>({
    companyId: '', entityType: '', action: '', actor: '',
    dateFrom: '', dateTo: '', page: 1, limit: 10,
  });
  const [diffEntry, setDiffEntry] = useState<AuditEntry | null>(null);
  const { data, isLoading, isError, refetch } = useAdminAudit(filters);

  const entries = data?.data ?? [];
  const meta = data?.meta;
  const columns = getAuditColumns(setDiffEntry);

  const handleFilterChange = useCallback((key: string, value: string) => {
    setFilters((f) => ({ ...f, [key]: value, page: 1 }));
  }, []);

  const filterValues: Record<string, string> = {
    entityType: filters.entityType, action: filters.action,
    actor: filters.actor, dateFrom: filters.dateFrom, dateTo: filters.dateTo,
  };

  const handleExport = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (filters.entityType) params.entityType = filters.entityType;
      if (filters.action) params.action = filters.action;
      if (filters.actor) params.actor = filters.actor;
      if (filters.dateFrom) params.dateFrom = filters.dateFrom;
      if (filters.dateTo) params.dateTo = filters.dateTo;

      const response = await api.get('/admin/audit/export', { params, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data as BlobPart]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-log-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch { /* interceptor handles */ }
  }, [filters]);

  if (isLoading) return <PageLoader />;
  if (isError) return <PageError onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit Log" subtitle="Platform-wide activity trail"
        actions={<Button variant="secondary" icon={<Download className="h-4 w-4" />} onClick={handleExport}>Export CSV</Button>}
      />

      <FilterBar filters={AUDIT_FILTER_CONFIGS} values={filterValues} onChange={handleFilterChange} />
      <DataTable columns={columns} data={entries} loading={isLoading} empty="No audit entries found" />

      <div className="lg:hidden grid grid-cols-1 gap-3">
        {entries.map((e) => (
          <div key={e.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-medium text-gray-100">{e.actor}</p>
              <span className="text-xs text-gray-500">{formatDate(e.timestamp)}</span>
            </div>
            <p className="text-xs text-gray-400">{e.action} · {e.entityType} · <span className="text-gray-500">{e.companyName}</span></p>
            {e.diff && <Button variant="ghost" size="sm" onClick={() => setDiffEntry(e)} className="mt-2">View changes</Button>}
          </div>
        ))}
      </div>

      {meta && (
        <Pagination total={meta.total} page={filters.page} limit={filters.limit}
          onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
          onLimitChange={(l) => setFilters((f) => ({ ...f, limit: l, page: 1 }))} />
      )}

      {diffEntry && <AuditDiffModal entry={diffEntry} open={!!diffEntry} onClose={() => setDiffEntry(null)} />}
    </div>
  );
};
