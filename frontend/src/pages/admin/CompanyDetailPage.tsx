import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useCompanyDetail } from '@/hooks/useAdmin';
import { Tabs, StatusBadge, PageLoader, PageError } from '@/components/ui';
import { formatCurrency, formatDate } from '@/lib/utils';
import { CompanyOverviewTab } from './CompanyOverviewTab';
import { CompanySubscriptionsTab } from './CompanySubscriptionsTab';
import { CompanyCustomersTab } from './CompanyCustomersTab';
import { CompanyInvoicesTab } from './CompanyInvoicesTab';
import { CompanyAuditTab } from './CompanyAuditTab';
import type { TabItem } from '@/types';

const TABS: TabItem[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'subscriptions', label: 'Subscriptions' },
  { key: 'customers', label: 'Customers' },
  { key: 'invoices', label: 'Invoices' },
  { key: 'audit', label: 'Audit Log' },
];

export const CompanyDetailPage: React.FC = () => {
  const { tenantId = '' } = useParams<{ tenantId: string }>();
  const [activeTab, setActiveTab] = useState('overview');
  const { data: company, isLoading, isError, refetch } = useCompanyDetail(tenantId);

  if (isLoading) return <PageLoader />;
  if (isError || !company) return <PageError onRetry={refetch} />;

  return (
    <div className="space-y-0">
      {/* Company banner */}
      <div className="bg-teal-500/10 border border-teal-500/20 rounded-xl p-4 sm:p-5 mb-6">
        <Link
          to="/admin/companies"
          className="inline-flex items-center gap-1.5 text-sm text-teal-400 hover:text-teal-300 mb-3 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to companies
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-xl bg-teal-500/20 border border-teal-500/30 flex items-center justify-center">
              <span className="text-lg font-bold text-teal-400">
                {company.name.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-50">
                Viewing {company.name}
              </h1>
              <p className="text-sm text-gray-400">{company.slug}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={company.status} />
            <span className="text-sm text-gray-400">
              {formatCurrency(company.mrr)}/mo
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs tabs={TABS} active={activeTab} onChange={setActiveTab} className="mb-6" />

      {/* Tab content */}
      {activeTab === 'overview' && <CompanyOverviewTab company={company} />}
      {activeTab === 'subscriptions' && <CompanySubscriptionsTab tenantId={tenantId} />}
      {activeTab === 'customers' && <CompanyCustomersTab tenantId={tenantId} />}
      {activeTab === 'invoices' && <CompanyInvoicesTab tenantId={tenantId} />}
      {activeTab === 'audit' && <CompanyAuditTab tenantId={tenantId} />}
    </div>
  );
};
