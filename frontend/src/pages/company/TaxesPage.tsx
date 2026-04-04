import React, { useState } from 'react';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { useTaxes, useDeleteTax } from '@/hooks/useTaxes';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import type { Tax } from '@/types/company';
import type { Column } from '@/types';
import {
  PageHeader, DataTable, Button,
  ConfirmModal, PageLoader, MobileCard,
} from '@/components/ui';
import { TaxForm } from './TaxForm';

export const TaxesPage: React.FC = () => {
  const [formOpen, setFormOpen] = useState(false);
  const [editTax, setEditTax] = useState<Tax | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Tax | null>(null);

  const { data, isLoading } = useTaxes();
  const deleteMutation = useDeleteTax();
  const { isMobile } = useBreakpoint();

  const taxes = data?.data ?? [];

  const columns: Column<Tax>[] = [
    { key: 'name', header: 'Name', sortable: true },
    {
      key: 'rate',
      header: 'Rate (%)',
      sortable: true,
      render: (row) => (
        <span className="tabular-nums">{row.rate}%</span>
      ),
    },
    { key: 'type', header: 'Type' },
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

  const openEdit = (tax: Tax) => {
    setEditTax(tax);
    setFormOpen(true);
  };

  const openCreate = () => {
    setEditTax(null);
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
        title="Taxes"
        subtitle="Configure tax rates for invoicing"
        actions={
          <Button icon={<Plus className="h-4 w-4" />} onClick={openCreate}>
            New tax
          </Button>
        }
      />

      <DataTable columns={columns} data={taxes} />

      {isMobile && (
        <div className="space-y-3 lg:hidden">
          {taxes.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No taxes configured</div>
          ) : (
            taxes.map((t) => (
              <MobileCard
                key={t.id}
                title={t.name}
                subtitle={t.type}
                fields={[
                  { label: 'Rate', value: `${t.rate}%` },
                ]}
                trailing={
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => openEdit(t)}
                      className="h-9 w-9 flex items-center justify-center rounded-lg
                                 text-gray-400 hover:text-violet-400 transition-colors"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setDeleteTarget(t)}
                      className="h-9 w-9 flex items-center justify-center rounded-lg
                                 text-gray-400 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                }
              />
            ))
          )}
        </div>
      )}

      {/* No pagination — usually < 10 rows */}

      {formOpen && (
        <TaxForm
          open={formOpen}
          onClose={() => setFormOpen(false)}
          tax={editTax}
        />
      )}

      <ConfirmModal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete tax"
        message={`Delete "${deleteTarget?.name}"? Existing invoices using this tax will not be affected.`}
        confirmLabel="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  );
};
