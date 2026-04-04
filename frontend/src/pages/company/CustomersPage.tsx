import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, ChevronRight, UserPlus } from 'lucide-react';
import { useCustomers } from '@/hooks/useCustomers';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { formatDate } from '@/lib/utils';
import type { Customer } from '@/types/company';
import type { Column } from '@/types';
import {
  PageHeader, DataTable, StatusBadge, Button,
  Pagination, PageLoader, MobileCard,
} from '@/components/ui';
import { InviteCustomerModal } from './InviteCustomerModal';

function getChurnLevel(score: number): string {
  if (score >= 70) return 'high';
  if (score >= 30) return 'medium';
  return 'low';
}

export const CustomersPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [inviteOpen, setInviteOpen] = useState(false);
  const { isMobile } = useBreakpoint();

  const { data, isLoading } = useCustomers(page, limit);

  const customers = data?.data ?? [];
  const total = data?.meta?.total ?? customers.length;

  const columns: Column<Customer>[] = [
    { key: 'name', header: 'Name', sortable: true },
    { key: 'email', header: 'Email', sortable: true },
    {
      key: 'plan_name',
      header: 'Plan',
      render: (row) => row.plan_name || <span className="text-gray-600">—</span>,
    },
    {
      key: 'subscription_status',
      header: 'Sub Status',
      render: (row) =>
        row.subscription_status ? (
          <StatusBadge status={row.subscription_status} />
        ) : (
          <span className="text-gray-600">—</span>
        ),
    },
    {
      key: 'churn_score',
      header: 'Churn Risk',
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-2">
          <StatusBadge status={getChurnLevel(row.churn_score)} />
          <span className="text-xs text-gray-500 tabular-nums">
            {row.churn_score}%
          </span>
        </div>
      ),
    },
    {
      key: 'last_invoice_date',
      header: 'Last Invoice',
      render: (row) =>
        row.last_invoice_date ? formatDate(row.last_invoice_date) : '—',
    },
    {
      key: 'actions',
      header: '',
      width: '80px',
      render: (row) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/company/customers/${row.id}`);
          }}
          className="h-8 px-3 flex items-center gap-1.5 rounded-lg text-xs
                     text-gray-400 hover:text-violet-400 hover:bg-violet-500/10 transition-colors"
        >
          View <ChevronRight className="h-3.5 w-3.5" />
        </button>
      ),
    },
  ];

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customers"
        subtitle="Manage your customer base and monitor churn"
        actions={
          <Button icon={<UserPlus className="h-4 w-4" />} onClick={() => setInviteOpen(true)}>
            Invite customer
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={customers}
        onRowClick={(row) => navigate(`/company/customers/${row.id}`)}
      />

      {isMobile && (
        <div className="space-y-3 lg:hidden">
          {customers.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No customers yet</div>
          ) : (
            customers.map((c) => (
              <MobileCard
                key={c.id}
                title={c.name}
                subtitle={c.email}
                onClick={() => navigate(`/company/customers/${c.id}`)}
                fields={[
                  {
                    label: 'Status',
                    value: c.subscription_status
                      ? <StatusBadge status={c.subscription_status} />
                      : '—',
                  },
                  {
                    label: 'Churn',
                    value: (
                      <div className="flex items-center gap-1">
                        <StatusBadge status={getChurnLevel(c.churn_score)} />
                        <span className="text-xs text-gray-500">{c.churn_score}%</span>
                      </div>
                    ),
                  },
                ]}
                trailing={<ChevronRight className="h-4 w-4 text-gray-600" />}
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

      <InviteCustomerModal open={inviteOpen} onClose={() => setInviteOpen(false)} />
    </div>
  );
};
