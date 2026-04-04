import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { useCompanyDashboard } from '@/hooks/useDashboard';
import { useAuthStore } from '@/stores/authStore';
import { formatCurrency, formatRelativeTime } from '@/lib/utils';
import {
  PageHeader, StatCard, PageLoader, StatusBadge,
} from '@/components/ui';
import { DashboardChurnPanel } from './DashboardChurnPanel';
import { DashboardDunningPanel } from './DashboardDunningPanel';

const CHART_TOOLTIP_STYLE = {
  contentStyle: {
    background: '#111827',
    border: '1px solid #374151',
    borderRadius: '8px',
    fontSize: '12px',
    color: '#e5e7eb',
  },
};

export const CompanyDashboard: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const { data, isLoading } = useCompanyDashboard();

  if (isLoading) return <PageLoader />;

  const m = data?.metrics ?? {};
  const subs = m['active_subscriptions'];
  const mrr = m['mrr'];
  const arr = m['arr'];
  const overdue = m['overdue_invoices'];

  const subsChart = data?.subscriptions_chart ?? [];
  const mrrChart = data?.mrr_chart ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle={`Welcome back, ${user?.name ?? 'there'}`}
      />

      {/* Row 1 — Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Subscriptions"
          value={subs?.value ?? '—'}
          change={subs?.delta ? { value: parseFloat(subs.delta), positive: subs.trend === 'up' } : undefined}
          icon="Layers"
          color="teal"
        />
        <StatCard
          label="MRR"
          value={mrr?.value ?? '—'}
          change={mrr?.delta ? { value: parseFloat(mrr.delta), positive: mrr.trend === 'up' } : undefined}
          icon="TrendingUp"
          color="violet"
        />
        <StatCard
          label="ARR"
          value={arr?.value ?? '—'}
          icon="BarChart3"
          color="blue"
        />
        <StatCard
          label="Overdue Invoices"
          value={overdue?.value ?? '0'}
          change={overdue?.delta ? { value: parseFloat(overdue.delta), positive: false } : undefined}
          icon="AlertCircle"
          color={Number(overdue?.raw_value ?? 0) > 0 ? 'rose' : 'teal'}
        />
      </div>

      {/* Row 2 — Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">New subscriptions</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={subsChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip {...CHART_TOOLTIP_STYLE} />
              <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">MRR over time</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={mrrChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false}
                tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip {...CHART_TOOLTIP_STYLE} formatter={(v: number) => [formatCurrency(v), 'MRR']} />
              <Line type="monotone" dataKey="mrr" stroke="#2dd4bf" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 3 — Churn + Dunning panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DashboardChurnPanel customers={data?.at_risk_customers ?? []} />
        <DashboardDunningPanel entries={data?.active_dunning ?? []} />
      </div>

      {/* Row 4 — Recent activity */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Recent activity</h3>
        {(data?.recent_activity ?? []).length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No recent activity</p>
        ) : (
          <div className="divide-y divide-gray-800/50">
            {(data?.recent_activity ?? []).slice(0, 5).map((a) => (
              <div key={a.id} className="flex items-center gap-3 py-3">
                <ActivityDot action={a.action} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-200 truncate">{a.description}</p>
                  <p className="text-xs text-gray-500">{a.entity_type}</p>
                </div>
                <span className="text-xs text-gray-500 shrink-0">
                  {formatRelativeTime(a.created_at)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const ActivityDot: React.FC<{ action: string }> = ({ action }) => {
  const colorMap: Record<string, string> = {
    create: 'bg-emerald-400',
    update: 'bg-amber-400',
    delete: 'bg-red-400',
    status_change: 'bg-blue-400',
  };
  return (
    <span className={`h-2 w-2 rounded-full shrink-0 ${colorMap[action] ?? 'bg-gray-500'}`} />
  );
};
