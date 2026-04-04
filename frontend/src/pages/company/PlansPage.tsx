import React, { useState } from 'react';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { usePlans, useDeletePlan } from '@/hooks/usePlans';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Plan } from '@/types/company';
import type { Column } from '@/types';
import {
  PageHeader, DataTable, StatusBadge, Button,
  ConfirmModal, Pagination, PageLoader, MobileCard,
} from '@/components/ui';
import { PlanForm } from './PlanForm';

export const PlansPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [formOpen, setFormOpen] = useState(false);
  const [editPlan, setEditPlan] = useState<Plan | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Plan | null>(null);

  const { data, isLoading } = usePlans(page, limit);
  const deleteMutation = useDeletePlan();
  const { isMobile } = useBreakpoint();

  const plans = data?.data ?? [];
  const total = data?.meta?.total ?? plans.length;

  const isExpired = (plan: Plan) => {
    if (!plan.end_date) return false;
    return new Date(plan.end_date) < new Date();
  };

  const columns: Column<Plan>[] = [
    { key: 'name', header: 'Name', sortable: true },
    {
      key: 'price',
      header: 'Price',
      sortable: true,
      render: (row) => (
        <span>
          {formatCurrency(row.price)}
          <span className="text-gray-500 text-xs ml-1">/ {row.billing_period}</span>
        </span>
      ),
    },
    {
      key: 'billing_period',
      header: 'Period',
      render: (row) => <StatusBadge status={row.billing_period} />,
    },
    {
      key: 'start_date',
      header: 'Start',
      render: (row) => formatDate(row.start_date),
    },
    {
      key: 'end_date',
      header: 'End',
      render: (row) => row.end_date ? formatDate(row.end_date) : '—',
    },
    {
      key: 'subscriptions_count',
      header: 'Subscriptions',
      sortable: true,
      render: (row) => (
        <span className="text-gray-400">{row.subscriptions_count ?? 0}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '120px',
      render: (row) => (
        <div className="flex items-center gap-1 justify-end">
          <button
            onClick={(e) => { e.stopPropagation(); openEdit(row); }}
            className="h-8 w-8 flex items-center justify-center rounded-lg
                       text-gray-400 hover:text-violet-400 hover:bg-violet-500/10 transition-colors"
            aria-label="Edit"
          >
            <Pencil className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); setDeleteTarget(row); }}
            className="h-8 w-8 flex items-center justify-center rounded-lg
                       text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            aria-label="Delete"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      ),
    },
  ];

  const openEdit = (plan: Plan) => {
    setEditPlan(plan);
    setFormOpen(true);
  };

  const openCreate = () => {
    setEditPlan(null);
    setFormOpen(true);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    await deleteMutation.mutateAsync(deleteTarget.id);
    setDeleteTarget(null);
  };

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Recurring plans"
        subtitle="Configure billing plans for your subscriptions"
        actions={
          <Button icon={<Plus className="h-4 w-4" />} onClick={openCreate}>
            New plan
          </Button>
        }
      />

      <DataTable columns={columns} data={plans} />

      {isMobile && (
        <div className="space-y-3 lg:hidden">
          {plans.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No plans yet</div>
          ) : (
            plans.map((p) => (
              <MobileCard
                key={p.id}
                title={p.name}
                subtitle={
                  <span className="text-sm text-teal-400 font-semibold">
                    {formatCurrency(p.price)}/{p.billing_period}
                  </span>
                }
                fields={[
                  {
                    label: 'Status',
                    value: <StatusBadge status={isExpired(p) ? 'expired' : 'active'} />,
                  },
                  { label: 'Subs', value: String(p.subscriptions_count ?? 0) },
                ]}
                trailing={
                  <button
                    onClick={() => openEdit(p)}
                    className="h-9 w-9 flex items-center justify-center rounded-lg
                               text-gray-400 hover:text-violet-400 transition-colors"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                }
              />
            ))
          )}
        </div>
      )}

      {total > limit && (
        <Pagination
          total={total}
          page={page}
          limit={limit}
          onPageChange={setPage}
          onLimitChange={(l) => { setLimit(l); setPage(1); }}
        />
      )}

      {formOpen && (
        <PlanForm
          open={formOpen}
          onClose={() => setFormOpen(false)}
          plan={editPlan}
        />
      )}

      <ConfirmModal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete plan"
        message={`Delete "${deleteTarget?.name}"? Active subscriptions using this plan may be affected.`}
        confirmLabel="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  );
};
