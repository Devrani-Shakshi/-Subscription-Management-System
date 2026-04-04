import React, { useState } from 'react';
import { Download } from 'lucide-react';
import { useCompanyAudit, useAuditExportUrl } from '@/hooks/useAudit';
import { api } from '@/lib/axios';
import type { AuditLogEntry, AuditFilters, AuditAction, DiffField } from '@/types/company';
import type { FilterConfig } from '@/types';
import {
  PageHeader, FilterBar, Pagination, PageLoader, Button, DiffModal,
} from '@/components/ui';
import { AuditTimeline } from './AuditTimeline';

const ENTITY_OPTIONS = [
  { label: 'All', value: '' },
  { label: 'Subscription', value: 'subscription' },
  { label: 'Invoice', value: 'invoice' },
  { label: 'Payment', value: 'payment' },
  { label: 'Plan', value: 'plan' },
  { label: 'Product', value: 'product' },
  { label: 'Customer', value: 'customer' },
  { label: 'Discount', value: 'discount' },
];

const ACTION_OPTIONS = [
  { label: 'All', value: '' },
  { label: 'Create', value: 'create' },
  { label: 'Update', value: 'update' },
  { label: 'Delete', value: 'delete' },
  { label: 'Status Change', value: 'status_change' },
];

export const AuditPage: React.FC = () => {
  const [filters, setFilters] = useState<AuditFilters>({
    page: 1,
    page_size: 50,
  });
  const [filterValues, setFilterValues] = useState<Record<string, string>>({
    entity_type: '',
    action: '',
  });
  const [diffModal, setDiffModal] = useState<{
    open: boolean;
    diff: Record<string, DiffField>;
  }>({ open: false, diff: {} });

  const { data, isLoading } = useCompanyAudit({
    ...filters,
    entity_type: filterValues.entity_type || undefined,
    action: filterValues.action || undefined,
  });

  const entries = data?.data ?? [];
  const total = data?.meta?.total ?? entries.length;

  const exportUrl = useAuditExportUrl({
    entity_type: filterValues.entity_type || undefined,
    action: filterValues.action || undefined,
  });

  const handleExport = async () => {
    const { data: blob } = await api.get(exportUrl, { responseType: 'blob' });
    const url = window.URL.createObjectURL(blob as Blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'audit_log.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilterValues((prev) => ({ ...prev, [key]: value }));
    setFilters((prev) => ({ ...prev, page: 1 }));
  };

  const handleViewDiff = (entry: AuditLogEntry) => {
    setDiffModal({ open: true, diff: entry.diff_json });
  };

  const filterConfigs: FilterConfig[] = [
    { key: 'entity_type', label: 'Entity', type: 'select', options: ENTITY_OPTIONS },
    { key: 'action', label: 'Action', type: 'select', options: ACTION_OPTIONS },
  ];

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit trail"
        actions={
          <Button
            variant="secondary"
            icon={<Download className="h-4 w-4" />}
            onClick={handleExport}
          >
            Export CSV
          </Button>
        }
      />

      <FilterBar
        filters={filterConfigs}
        values={filterValues}
        onChange={handleFilterChange}
      />

      <AuditTimeline entries={entries} onViewDiff={handleViewDiff} />

      {total > filters.page_size && (
        <Pagination
          total={total}
          page={filters.page}
          limit={filters.page_size}
          onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
          onLimitChange={(l) => setFilters((f) => ({ ...f, page_size: l, page: 1 }))}
        />
      )}

      <DiffModal
        open={diffModal.open}
        onClose={() => setDiffModal({ open: false, diff: {} })}
        diff={diffModal.diff}
      />
    </div>
  );
};
