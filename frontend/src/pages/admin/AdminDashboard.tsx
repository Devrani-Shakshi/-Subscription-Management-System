import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAdminDashboard } from '@/hooks/useAdmin';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { PageHeader, StatCard, PageLoader, PageError, Button } from '@/components/ui';
import { formatCurrency } from '@/lib/utils';
import { AlertCard, CompanyCard, getCompanyColumns } from './DashboardWidgets';
import type { AdminCompanySummary } from '@/types/admin';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();
  const { data, isLoading, isError, refetch } = useAdminDashboard();

  const handleViewCompany = (id: string) =>
    navigate(`/admin/companies/${id}`);

  if (isLoading) return <PageLoader />;
  if (isError || !data) return <PageError onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader title="Platform overview" subtitle={`${data.newCompaniesThisMonth} new companies this month`} />

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Companies" value={data.totalCompanies} icon="Building2" color="violet" />
        <StatCard label="Active Subscriptions" value={data.totalActiveSubs.toLocaleString()} icon="RefreshCw" color="teal" />
        <StatCard label="Platform MRR" value={formatCurrency(data.platformMRR)} icon="TrendingUp" color="blue" />
        <StatCard label="Churn Rate" value={`${data.platformChurnRate}%`} icon="UserMinus" color="rose" />
      </div>

      {/* Alerts */}
      {data.alerts.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Alerts ({data.alerts.length})
          </h2>
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-hide">
            {data.alerts.map((alert) => (
              <AlertCard key={alert.id} alert={alert} onView={handleViewCompany} />
            ))}
          </div>
        </div>
      )}

      {/* Top Companies */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            Top Companies
          </h2>
          <Button variant="ghost" size="sm" onClick={() => navigate('/admin/companies')}>
            View all
          </Button>
        </div>

        {/* Desktop Table */}
        {!isMobile && (
          <div className="hidden lg:block overflow-x-auto rounded-xl border border-gray-800 bg-gray-900/50">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  {getCompanyColumns(handleViewCompany).map((col) => (
                    <th key={col.key} className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      {col.header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.topCompanies.map((company) => (
                  <tr key={company.id} className="border-b border-gray-800/30 last:border-0 hover:bg-gray-800/40 transition-colors">
                    {getCompanyColumns(handleViewCompany).map((col) => (
                      <td key={col.key} className="px-4 py-3 text-gray-200">
                        {col.render ? col.render(company) : (company[col.key as keyof AdminCompanySummary] as React.ReactNode) ?? '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Mobile Cards */}
        <div className="lg:hidden grid grid-cols-1 sm:grid-cols-2 gap-3">
          {data.topCompanies.map((company) => (
            <CompanyCard key={company.id} company={company} onView={handleViewCompany} />
          ))}
        </div>
      </div>
    </div>
  );
};
