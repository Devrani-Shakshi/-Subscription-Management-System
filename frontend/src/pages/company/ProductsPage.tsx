import React, { useState } from 'react';
import { Plus, Pencil, Trash2, Package } from 'lucide-react';
import { useProducts, useDeleteProduct } from '@/hooks/useProducts';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { formatCurrency } from '@/lib/utils';
import type { Product } from '@/types/company';
import type { Column } from '@/types';
import {
  PageHeader, DataTable, StatusBadge, Button,
  ConfirmModal, Pagination, PageLoader, MobileCard,
} from '@/components/ui';
import { ProductForm } from './ProductForm';

export const ProductsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [formOpen, setFormOpen] = useState(false);
  const [editProduct, setEditProduct] = useState<Product | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);

  const { data, isLoading } = useProducts(page, limit);
  const deleteMutation = useDeleteProduct();
  const { isMobile } = useBreakpoint();

  const products = data?.data ?? [];
  const total = data?.meta?.total ?? products.length;

  const columns: Column<Product>[] = [
    { key: 'name', header: 'Name', sortable: true },
    {
      key: 'type',
      header: 'Type',
      render: (row) => <StatusBadge status={row.type} />,
    },
    {
      key: 'sales_price',
      header: 'Sales Price',
      sortable: true,
      render: (row) => formatCurrency(row.sales_price),
    },
    {
      key: 'cost_price',
      header: 'Cost Price',
      render: (row) => formatCurrency(row.cost_price),
    },
    {
      key: 'variants',
      header: 'Variants',
      render: (row) => (
        <span className="text-gray-400">{row.variants?.length ?? 0}</span>
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

  const openEdit = (product: Product) => {
    setEditProduct(product);
    setFormOpen(true);
  };

  const openCreate = () => {
    setEditProduct(null);
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
        title="Products"
        subtitle="Manage your product catalog"
        actions={
          <Button
            icon={<Plus className="h-4 w-4" />}
            onClick={openCreate}
          >
            New product
          </Button>
        }
      />

      {/* Desktop table */}
      <DataTable columns={columns} data={products} />

      {/* Mobile cards */}
      {isMobile && (
        <div className="space-y-3 lg:hidden">
          {products.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No products yet</div>
          ) : (
            products.map((p) => (
              <MobileCard
                key={p.id}
                title={p.name}
                subtitle={<StatusBadge status={p.type} />}
                fields={[
                  { label: 'Price', value: formatCurrency(p.sales_price) },
                  { label: 'Variants', value: String(p.variants?.length ?? 0) },
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

      {/* Product Form Modal */}
      {formOpen && (
        <ProductForm
          open={formOpen}
          onClose={() => setFormOpen(false)}
          product={editProduct}
        />
      )}

      {/* Delete Confirmation */}
      <ConfirmModal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete product"
        message={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  );
};
