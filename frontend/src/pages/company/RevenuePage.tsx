import React, { useState } from 'react';
import { PageHeader, StatCard, DatePicker, PageLoader, PageError } from '@/components/ui';
import { useRevenue } from '@/hooks/useRevenue';
import { formatCurrency } from '@/lib/utils';
import type { RevenueFilters } from '@/types/billing';
import { RevenueChart } from './revenue/RevenueChart';
import { RevenueTable } from './revenue/RevenueTable';

export const RevenuePage: React.FC = () => {
  const [filters, setFilters] = useState<RevenueFilters>({});
  const { data, isLoading, isError, refetch } = useRevenue(filters);

  const revenue = data?.data;
  const summary = revenue?.summary;
  const timeline = revenue?.timeline ?? [];

  if (isLoading) return <PageLoader />;
  if (isError) return <PageError onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Revenue recognition"
        subtitle="Track recognized, deferred, and cumulative revenue"
        actions={
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">From</span>
              <DatePicker
                value={filters.dateFrom ?? ''}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, dateFrom: e.target.value || undefined }))
                }
                className="w-36"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">To</span>
              <DatePicker
                value={filters.dateTo ?? ''}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, dateTo: e.target.value || undefined }))
                }
                className="w-36"
              />
            </div>
          </div>
        }
      />

      {/* Top stat cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            label="Recognized this month"
            value={formatCurrency(summary.recognizedThisMonth)}
            icon="TrendingUp"
            color="violet"
          />
          <StatCard
            label="Deferred"
            value={formatCurrency(summary.deferred)}
            icon="Clock"
            color="teal"
          />
          <StatCard
            label="Cumulative YTD"
            value={formatCurrency(summary.cumulativeYTD)}
            icon="BarChart3"
            color="amber"
          />
        </div>
      )}

      {/* Chart */}
      {timeline.length > 0 && <RevenueChart data={timeline} />}

      {/* Breakdown table */}
      {timeline.length > 0 && <RevenueTable data={timeline} />}
    </div>
  );
};
