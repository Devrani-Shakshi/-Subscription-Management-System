import React from 'react';
import { PageHeader, StatCard } from '@/components/ui';

export const PortalDashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <PageHeader
        title="My Subscription"
        subtitle="Manage your subscription and billing"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Current Plan"
          value="Pro"
          icon="Layers"
          color="amber"
        />
        <StatCard
          label="Next Billing"
          value="Apr 15"
          icon="Calendar"
          color="blue"
        />
        <StatCard
          label="Monthly Cost"
          value="$49/mo"
          icon="CreditCard"
          color="teal"
        />
        <StatCard
          label="Status"
          value="Active"
          icon="CheckCircle"
          color="violet"
        />
      </div>

      <div className="glass-card p-6 min-h-[200px] flex items-center justify-center">
        <p className="text-gray-500">Subscription details and usage coming soon</p>
      </div>
    </div>
  );
};
