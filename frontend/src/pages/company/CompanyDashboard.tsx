import React from 'react';
import { PageHeader, StatCard } from '@/components/ui';

export const CompanyDashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Company Dashboard"
        subtitle="Your subscription business at a glance"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Plans"
          value={8}
          icon="Layers"
          color="teal"
        />
        <StatCard
          label="Subscribers"
          value={356}
          change={{ value: 14, positive: true }}
          icon="Users"
          color="violet"
        />
        <StatCard
          label="MRR"
          value="$12,480"
          change={{ value: 6.8, positive: true }}
          icon="TrendingUp"
          color="blue"
        />
        <StatCard
          label="Overdue Invoices"
          value={7}
          change={{ value: 2, positive: false }}
          icon="AlertCircle"
          color="rose"
        />
      </div>

      <div className="glass-card p-6 min-h-[300px] flex items-center justify-center">
        <p className="text-gray-500">Revenue charts and subscription metrics coming soon</p>
      </div>
    </div>
  );
};
