import React, { useState } from 'react';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { useTemplates, useDeleteTemplate } from '@/hooks/useTemplates';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import type { Template } from '@/types/company';
import type { Column } from '@/types';
import {
  PageHeader, DataTable, Button,
  ConfirmModal, Pagination, PageLoader, MobileCard,
} from '@/components/ui';
import { TemplateForm } from './TemplateForm';

export const TemplatesPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [formOpen, setFormOpen] = useState(false);
  const [editTemplate, setEditTemplate] = useState<Template | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Template | null>(null);

  const { data, isLoading } = useTemplates(page, limit);
  const deleteMutation = useDeleteTemplate();
  const { isMobile } = useBreakpoint();

  const templates = data?.data ?? [];
  const total = data?.meta?.total ?? templates.length;

  const columns: Column<Template>[] = [
    { key: 'name', header: 'Name', sortable: true },
    { key: 'plan_name', header: 'Plan' },
    {
      key: 'validity_days',
      header: 'Validity',
      render: (row) => `${row.validity_days} days`,
    },
    {
      key: 'product_lines',
      header: 'Products',
      render: (row) => (
        <span className="text-gray-400">
          {row.product_lines?.length ?? 0}
        </span>
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

  const openEdit = (tpl: Template) => {
    setEditTemplate(tpl);
    setFormOpen(true);
  };

  const openCreate = () => {
    setEditTemplate(null);
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
        title="Quotation Templates"
        subtitle="Pre-configured templates for quotations"
        actions={
          <Button icon={<Plus className="h-4 w-4" />} onClick={openCreate}>
            New template
          </Button>
        }
      />

      <DataTable columns={columns} data={templates} />

      {isMobile && (
        <div className="space-y-3 lg:hidden">
          {templates.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No templates yet</div>
          ) : (
            templates.map((t) => (
              <MobileCard
                key={t.id}
                title={t.name}
                subtitle={t.plan_name}
                fields={[
                  { label: 'Validity', value: `${t.validity_days} days` },
                  { label: 'Products', value: String(t.product_lines?.length ?? 0) },
                ]}
                trailing={
                  <button
                    onClick={() => openEdit(t)}
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
        <TemplateForm
          open={formOpen}
          onClose={() => setFormOpen(false)}
          template={editTemplate}
        />
      )}

      <ConfirmModal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete template"
        message={`Delete "${deleteTarget?.name}"? This cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  );
};
