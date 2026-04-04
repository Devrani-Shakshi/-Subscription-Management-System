import React, { useState } from 'react';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { useDiscounts, useDeleteDiscount } from '@/hooks/useDiscounts';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Discount } from '@/types/company';
import type { Column } from '@/types';
import {
  PageHeader, DataTable, StatusBadge, Button,
  ConfirmModal, Pagination, PageLoader, MobileCard, ProgressBar,
} from '@/components/ui';
import { DiscountForm } from './DiscountForm';

export const DiscountsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [formOpen, setFormOpen] = useState(false);
  const [editDiscount, setEditDiscount] = useState<Discount | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Discount | null>(null);

  const { data, isLoading } = useDiscounts(page, limit);
  const deleteMutation = useDeleteDiscount();
  const { isMobile } = useBreakpoint();

  const discounts = data?.data ?? [];
  const total = data?.meta?.total ?? discounts.length;

  const columns: Column<Discount>[] = [
    { key: 'name', header: 'Name', sortable: true },
    {
      key: 'type',
      header: 'Type',
      render: (row) => <StatusBadge status={row.type} />,
    },
    {
      key: 'value',
      header: 'Value',
      render: (row) =>
        row.type === 'percent'
          ? `${row.value}%`
          : formatCurrency(row.value),
    },
    {
      key: 'min_purchase',
      header: 'Min Purchase',
      render: (row) => formatCurrency(row.min_purchase),
    },
    {
      key: 'usage',
      header: 'Usage',
      render: (row) =>
        row.usage_limit ? (
          <ProgressBar value={row.used_count} max={row.usage_limit} />
        ) : (
          <span className="text-xs text-gray-500">Unlimited</span>
        ),
    },
    {
      key: 'end_date',
      header: 'Expires',
      render: (row) => (row.end_date ? formatDate(row.end_date) : '—'),
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

  const openEdit = (d: Discount) => {
    setEditDiscount(d);
    setFormOpen(true);
  };

  const openCreate = () => {
    setEditDiscount(null);
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
        title="Discounts"
        subtitle="Manage promotional codes and discounts"
        actions={
          <Button icon={<Plus className="h-4 w-4" />} onClick={openCreate}>
            New discount
          </Button>
        }
      />

      <DataTable columns={columns} data={discounts} />

      {isMobile && (
        <div className="space-y-3 lg:hidden">
          {discounts.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No discounts yet</div>
          ) : (
            discounts.map((d) => (
              <MobileCard
                key={d.id}
                title={d.name}
                subtitle={
                  <div className="flex items-center gap-2">
                    <StatusBadge status={d.type} />
                    <span className="text-sm font-semibold text-gray-200">
                      {d.type === 'percent' ? `${d.value}%` : formatCurrency(d.value)}
                    </span>
                  </div>
                }
                fields={[
                  {
                    label: 'Expires',
                    value: d.end_date ? formatDate(d.end_date) : 'Never',
                  },
                  {
                    label: 'Usage',
                    value: d.usage_limit ? (
                      <ProgressBar value={d.used_count} max={d.usage_limit} />
                    ) : (
                      'Unlimited'
                    ),
                  },
                ]}
                trailing={
                  <button
                    onClick={() => openEdit(d)}
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
        <DiscountForm
          open={formOpen}
          onClose={() => setFormOpen(false)}
          discount={editDiscount}
        />
      )}

      <ConfirmModal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete discount"
        message={`Delete "${deleteTarget?.name}"? This cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  );
};
