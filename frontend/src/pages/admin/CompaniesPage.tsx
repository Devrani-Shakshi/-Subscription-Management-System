import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { useCompanies, useSuspendCompany, useReactivateCompany } from '@/hooks/useAdmin';
import {
  PageHeader, DataTable, Button, SearchInput, Select,
  Pagination, ConfirmModal, PageLoader, PageError,
} from '@/components/ui';
import { CompanyCard } from './DashboardWidgets';
import { getCompaniesColumns } from './CompaniesColumns';
import { CreateCompanyModal } from './CreateCompanyModal';
import { DeleteCompanyModal } from './DeleteCompanyModal';
import type { AdminCompanySummary, AdminCompanyFilters } from '@/types/admin';

const STATUS_OPTIONS = [
  { label: 'All', value: '' },
  { label: 'Active', value: 'active' },
  { label: 'Trial', value: 'trial' },
  { label: 'Suspended', value: 'suspended' },
];

export const CompaniesPage: React.FC = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<AdminCompanyFilters>({ status: '', search: '', page: 1, limit: 10 });
  const [createOpen, setCreateOpen] = useState(false);
  const [suspendTarget, setSuspendTarget] = useState<AdminCompanySummary | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<AdminCompanySummary | null>(null);

  const { data, isLoading, isError, refetch } = useCompanies(filters);
  const suspendMutation = useSuspendCompany();
  const reactivateMutation = useReactivateCompany();

  const companies = data?.data ?? [];
  const meta = data?.meta;

  const updateFilter = useCallback(
    (key: keyof AdminCompanyFilters, value: string | number) => {
      setFilters((f) => ({ ...f, [key]: value, page: key === 'page' ? (value as number) : 1 }));
    }, []
  );

  const handleSuspendConfirm = useCallback(() => {
    if (!suspendTarget) return;
    const mutation = suspendTarget.status === 'suspended' ? reactivateMutation : suspendMutation;
    mutation.mutate(suspendTarget.id, { onSettled: () => setSuspendTarget(null) });
  }, [suspendTarget, suspendMutation, reactivateMutation]);

  const goTo = (id: string) => navigate(`/admin/companies/${id}`);
  const columns = getCompaniesColumns(goTo, setSuspendTarget, setDeleteTarget);

  if (isLoading) return <PageLoader />;
  if (isError) return <PageError onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Companies"
        subtitle={meta ? `${meta.total} companies` : undefined}
        actions={<Button variant="primary" icon={<Plus className="h-4 w-4" />} onClick={() => setCreateOpen(true)}>New company</Button>}
      />

      <div className="flex flex-col sm:flex-row gap-3">
        <Select options={STATUS_OPTIONS} value={filters.status} onChange={(e) => updateFilter('status', e.target.value)} placeholder="All statuses" className="sm:w-40" />
        <SearchInput value={filters.search} onChange={(v) => updateFilter('search', v)} placeholder="Search companies…" className="flex-1 sm:max-w-xs" />
      </div>

      <DataTable columns={columns} data={companies} loading={isLoading} empty="No companies found" />

      <div className="lg:hidden grid grid-cols-1 sm:grid-cols-2 gap-3">
        {companies.map((c) => (
          <CompanyCard key={c.id} company={c} onView={goTo} />
        ))}
      </div>

      {meta && (
        <Pagination total={meta.total} page={filters.page} limit={filters.limit} onPageChange={(p) => updateFilter('page', p)} onLimitChange={(l) => setFilters((f) => ({ ...f, limit: l, page: 1 }))} />
      )}

      <CreateCompanyModal open={createOpen} onClose={() => setCreateOpen(false)} />

      {suspendTarget && (
        <ConfirmModal
          open={!!suspendTarget}
          onClose={() => setSuspendTarget(null)}
          onConfirm={handleSuspendConfirm}
          title={suspendTarget.status === 'suspended' ? 'Reactivate Company' : 'Suspend Company'}
          message={suspendTarget.status === 'suspended' ? `Reactivate ${suspendTarget.name}? Users will regain access.` : `Suspending blocks all access for ${suspendTarget.name} and their customers.`}
          confirmLabel={suspendTarget.status === 'suspended' ? 'Reactivate' : 'Suspend'}
          variant={suspendTarget.status === 'suspended' ? 'primary' : 'danger'}
          loading={suspendMutation.isPending || reactivateMutation.isPending}
        />
      )}

      {deleteTarget && <DeleteCompanyModal company={deleteTarget} open={!!deleteTarget} onClose={() => setDeleteTarget(null)} />}
    </div>
  );
};
