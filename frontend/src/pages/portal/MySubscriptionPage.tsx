import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader, PageEmpty, PageError, PageLoader, StatusBadge, Button } from '@/components/ui';
import { useMySubscription, useTenantBranding } from '@/hooks/usePortal';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { formatCurrency, formatDate } from '@/lib/utils';
import { PlanSwitchModal } from './PlanSwitchModal';
import { CancelSubscriptionModal } from './CancelSubscriptionModal';
import { SubscriptionPlanCard } from './SubscriptionPlanCard';
import { OrderLinesCard } from './OrderLinesCard';
import { RecentInvoicesCard } from './RecentInvoicesCard';

export const MySubscriptionPage: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();
  const branding = useTenantBranding();
  const { data: subscription, isLoading, isError, refetch } = useMySubscription();

  const [switchOpen, setSwitchOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);

  if (isLoading) return <PageLoader />;
  if (isError) return <PageError onRetry={refetch} />;

  if (!subscription) {
    return (
      <div className="space-y-6">
        <PageHeader title="My Subscription" />
        <PageEmpty
          title="No active subscription"
          message="Choose a plan to get started."
          action={{
            label: 'Browse plans',
            onClick: () => navigate('/portal/plans'),
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Subscription"
        subtitle="Manage your plan and billing details"
      />

      <div className="max-w-2xl mx-auto space-y-5">
        {/* Scheduled downgrade banner */}
        {subscription.scheduledDowngrade && (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 px-4 py-3">
            <p className="text-sm text-amber-300">
              Plan change to{' '}
              <span className="font-semibold">{subscription.scheduledDowngrade.planName}</span>{' '}
              scheduled for{' '}
              <span className="font-semibold">
                {formatDate(subscription.scheduledDowngrade.effectiveDate)}
              </span>.
            </p>
          </div>
        )}

        {/* Plan card */}
        <SubscriptionPlanCard
          subscription={subscription}
          brandingColor={branding.primaryColor}
          onChangePlan={() => setSwitchOpen(true)}
          onCancel={() => setCancelOpen(true)}
          isMobile={isMobile}
        />

        {/* Order lines card */}
        <OrderLinesCard subscription={subscription} />

        {/* Recent invoices card */}
        <RecentInvoicesCard
          invoices={subscription.recentInvoices}
          onViewAll={() => navigate('/portal/invoices')}
        />
      </div>

      {/* Plan switch modal */}
      <PlanSwitchModal
        open={switchOpen}
        onClose={() => setSwitchOpen(false)}
        subscription={subscription}
      />

      {/* Cancel subscription modal */}
      <CancelSubscriptionModal
        open={cancelOpen}
        onClose={() => setCancelOpen(false)}
        subscription={subscription}
      />
    </div>
  );
};
