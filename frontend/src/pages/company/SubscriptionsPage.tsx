import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, ChevronDown } from 'lucide-react';
import {
  PageHeader,
  FilterBar,
  DataTable,
  Pagination,
  Button,
  StatusBadge,
  PageLoader,
  PageError,
} from '@/components/ui';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { useSubscriptions } from '@/hooks/useSubscriptions';
import { SubscriptionCardList } from './subscriptions/SubscriptionCardList';
import { BulkOperationModal } from './subscriptions/BulkOperationModal';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Column, FilterConfig } from '@/types';
import type { SubscriptionSummary, BulkAction } from '@/types/subscription';

const STATUS_OPTIONS = [
  { label: 'Draft', value: 'draft' },
  { label: 'Quotation', value: 'quotation' },
  { label: 'Confirmed', value: 'confirmed' },
  { label: 'Active', value: 'active' },
  { label: 'Paused', value: 'paused' },
  { label: 'Closed', value: 'closed' },
  { label: 'Cancelled', value: 'cancelled' },
];

const FILTER_CONFIG: FilterConfig[] = [
  { key: 'status', label: 'Status', type: 'select', options: STATUS_OPTIONS },
  { key: 'search', label: 'Customer', type: 'search' },
  { key: 'startFrom', label: 'Start from', type: 'date' },
  { key: 'expiryTo', label: 'Expires before', type: 'date' },
];

const BULK_OPTIONS: { label: string; value: BulkAction }[] = [
  { label: 'Activate', value: 'activate' },
  { label: 'Close', value: 'close' },
  { label: 'Apply discount', value: 'apply_discount' },
];

export const SubscriptionsPage: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();

  const [filters, setFilters] = useState({
    page: 1,
    limit: 10,
    status: '',
    search: '',
    startFrom: '',
    expiryTo: '',
  });
  const [selected, setSelected] = useState<string[]>([]);
  const [bulkAction, setBulkAction] = useState<BulkAction | null>(null);
  const [bulkDropdownOpen, setBulkDropdownOpen] = useState(false);

  const { data, isLoading, isError, refetch } = useSubscriptions({
    page: filters.page,
    limit: filters.limit,
    status: filters.status || undefined,
    search: filters.search || undefined,
    startFrom: filters.startFrom || undefined,
    expiryTo: filters.expiryTo || undefined,
  });

  const subscriptions = data?.data ?? [];
  const meta = data?.meta;

  const handleFilterChange = useCallback((key: string, value: string) => {
    setFilters((f) => ({ ...f, [key]: value, page: 1 }));
  }, []);

  const toggleSelect = useCallback((id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  }, []);

  const toggleSelectAll = useCallback(() => {
    if (selected.length === subscriptions.length) {
      setSelected([]);
    } else {
      setSelected(subscriptions.map((s) => s.id));
    }
  }, [selected.length, subscriptions]);

  const handleBulkAction = useCallback((action: BulkAction) => {
    setBulkAction(action);
    setBulkDropdownOpen(false);
  }, []);

  const columns: Column<SubscriptionSummary>[] = [
    {
      key: 'select',
      header: '',
      width: '40px',
      render: (row) => (
        <input
          type="checkbox"
          checked={selected.includes(row.id)}
          onChange={() => toggleSelect(row.id)}
          className="h-4 w-4 rounded border-gray-600 bg-gray-800 text-violet-500
                     focus:ring-violet-500/40 cursor-pointer"
          onClick={(e) => e.stopPropagation()}
        />
      ),
    },
    {
      key: 'number',
      header: '#',
      width: '120px',
      render: (row) => (
        <span className="font-mono text-sm text-violet-400">{row.number}</span>
      ),
    },
    { key: 'customerName', header: 'Customer' },
    {
      key: 'planName',
      header: 'Plan',
      render: (row) => (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md
                         bg-violet-500/10 text-violet-300 text-xs font-medium">
          {row.planName}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: 'startDate',
      header: 'Start',
      sortable: true,
      render: (row) => (
        <span className="text-gray-400 text-sm">{formatDate(row.startDate)}</span>
      ),
    },
    {
      key: 'expiryDate',
      header: 'Expiry',
      sortable: true,
      render: (row) => (
        <span className="text-gray-400 text-sm">{formatDate(row.expiryDate)}</span>
      ),
    },
    {
      key: 'mrr',
      header: 'MRR',
      sortable: true,
      render: (row) => (
        <span className="font-semibold text-emerald-400">
          {formatCurrency(row.mrr)}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '80px',
      render: (row) => (
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/company/subscriptions/${row.id}`);
            }}
            className="px-2 py-1 text-xs text-gray-400 hover:text-gray-200
                       hover:bg-gray-800 rounded transition-colors"
          >
            View
          </button>
        </div>
      ),
    },
  ];

  if (isError) {
    return <PageError message="Failed to load subscriptions" onRetry={refetch} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Subscriptions"
        subtitle="Manage customer subscriptions and recurring billing"
        breadcrumbs={[
          { label: 'Company', href: '/company' },
          { label: 'Subscriptions' },
        ]}
        actions={
          <div className="flex items-center gap-3">
            {/* Bulk action dropdown */}
            {selected.length > 0 && (
              <div className="relative">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setBulkDropdownOpen((o) => !o)}
                  icon={<ChevronDown className="h-4 w-4" />}
                >
                  Bulk action ({selected.length})
                </Button>
                {bulkDropdownOpen && (
                  <div className="absolute right-0 mt-1 w-48 bg-gray-900 border border-gray-800
                                  rounded-lg shadow-xl shadow-black/40 z-20 py-1">
                    {BULK_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => handleBulkAction(opt.value)}
                        className="w-full px-4 py-2 text-left text-sm text-gray-300
                                   hover:bg-gray-800 hover:text-gray-100 transition-colors"
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <Button
              variant="primary"
              icon={<Plus className="h-4 w-4" />}
              onClick={() => navigate('/company/subscriptions/new')}
            >
              {isMobile ? 'New' : 'New subscription'}
            </Button>
          </div>
        }
      />

      <FilterBar
        filters={FILTER_CONFIG}
        values={{
          status: filters.status,
          search: filters.search,
          startFrom: filters.startFrom,
          expiryTo: filters.expiryTo,
        }}
        onChange={handleFilterChange}
      />

      {isLoading ? (
        <PageLoader />
      ) : (
        <>
          {/* Desktop select-all row */}
          <div className="hidden lg:flex items-center gap-3 px-4 py-2">
            <input
              type="checkbox"
              checked={selected.length === subscriptions.length && subscriptions.length > 0}
              onChange={toggleSelectAll}
              className="h-4 w-4 rounded border-gray-600 bg-gray-800 text-violet-500
                         focus:ring-violet-500/40 cursor-pointer"
            />
            <span className="text-xs text-gray-500">
              {selected.length > 0
                ? `${selected.length} selected`
                : 'Select all'}
            </span>
          </div>

          <DataTable
            columns={columns}
            data={subscriptions}
            onRowClick={(row) => navigate(`/company/subscriptions/${row.id}`)}
            empty="No subscriptions found"
          />

          {isMobile && (
            <SubscriptionCardList
              subscriptions={subscriptions}
              onSelect={toggleSelect}
              selected={selected}
            />
          )}

          {meta && (
            <Pagination
              total={meta.total}
              page={filters.page}
              limit={filters.limit}
              onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
              onLimitChange={(l) => setFilters((f) => ({ ...f, limit: l, page: 1 }))}
            />
          )}
        </>
      )}

      {bulkAction && (
        <BulkOperationModal
          selectedIds={selected}
          action={bulkAction}
          onClose={() => setBulkAction(null)}
          onComplete={() => {
            setBulkAction(null);
            setSelected([]);
            refetch();
          }}
        />
      )}
    </div>
  );
};
