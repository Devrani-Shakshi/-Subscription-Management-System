import React from 'react';
import { PageHeader, StatCard } from '@/components/ui';

export const AdminDashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Admin Dashboard"
        subtitle="System-wide overview and management"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Companies"
          value={42}
          change={{ value: 12, positive: true }}
          icon="Building2"
          color="violet"
        />
        <StatCard
          label="Active Subscriptions"
          value="1,284"
          change={{ value: 8, positive: true }}
          icon="RefreshCw"
          color="teal"
        />
        <StatCard
          label="Monthly Revenue"
          value="$84,230"
          change={{ value: 5.2, positive: true }}
          icon="TrendingUp"
          color="blue"
        />
        <StatCard
          label="Churn Rate"
          value="2.1%"
          change={{ value: 0.3, positive: false }}
          icon="UserMinus"
          color="rose"
        />
      </div>

      <div className="glass-card p-6 min-h-[300px] flex items-center justify-center">
        <p className="text-gray-500">Dashboard charts and activity feed coming soon</p>
      </div>
    </div>
  );
};
