import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  PageHeader,
  PageLoader,
  PageError,
  StatusBadge,
  ConfirmModal,
} from '@/components/ui';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import {
  useSubscription,
  useTransitionSubscription,
} from '@/hooks/useSubscriptions';
import { SubscriptionInfoCard } from './subscriptions/detail/SubscriptionInfoCard';
import { OrderLinesTable } from './subscriptions/detail/OrderLinesTable';
import { InvoiceHistoryTable } from './subscriptions/detail/InvoiceHistoryTable';
import { TimelineCard } from './subscriptions/detail/TimelineCard';
import { ChurnRiskCard } from './subscriptions/detail/ChurnRiskCard';
import { DunningCard } from './subscriptions/detail/DunningCard';
import { UpgradeModal } from './subscriptions/detail/UpgradeModal';
import { DowngradeModal } from './subscriptions/detail/DowngradeModal';
import { StatusActionButtons } from './subscriptions/detail/StatusActionButtons';
import type { SubscriptionStatus } from '@/types/subscription';

export const SubscriptionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();

  const { data: subscription, isLoading, isError, refetch } = useSubscription(id ?? '');
  const transitionMutation = useTransitionSubscription();

  const [confirmTransition, setConfirmTransition] = useState<{
    to: SubscriptionStatus;
    label: string;
    variant: 'primary' | 'danger';
  } | null>(null);
  const [upgradeOpen, setUpgradeOpen] = useState(false);
  const [downgradeOpen, setDowngradeOpen] = useState(false);

  if (isLoading) return <PageLoader />;
  if (isError || !subscription) {
    return <PageError message="Failed to load subscription" onRetry={refetch} />;
  }

  const handleTransition = async () => {
    if (!confirmTransition) return;
    await transitionMutation.mutateAsync({
      id: subscription.id,
      payload: { to: confirmTransition.to },
    });
    setConfirmTransition(null);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={subscription.number}
        subtitle={subscription.customerName}
        breadcrumbs={[
          { label: 'Company', href: '/company' },
          { label: 'Subscriptions', href: '/company/subscriptions' },
          { label: subscription.number },
        ]}
        actions={
          <div className="flex items-center gap-2 flex-wrap">
            <StatusBadge status={subscription.status} />
            <StatusActionButtons
              status={subscription.status}
              pausable={subscription.pausable}
              renewable={subscription.renewable}
              onTransition={(to: SubscriptionStatus, label: string, variant: 'primary' | 'danger') =>
                setConfirmTransition({ to, label, variant })
              }
              onUpgrade={() => setUpgradeOpen(true)}
              onDowngrade={() => setDowngradeOpen(true)}
              onDelete={() =>
                setConfirmTransition({
                  to: 'cancelled',
                  label: 'Delete this draft?',
                  variant: 'danger',
                })
              }
            />
          </div>
        }
      />

      <div className={`grid gap-6 ${isMobile ? 'grid-cols-1' : 'grid-cols-3'}`}>
        {/* Left column (wider) */}
        <div className={`space-y-6 ${isMobile ? '' : 'col-span-2'}`}>
          <SubscriptionInfoCard subscription={subscription} />
          <OrderLinesTable orderLines={subscription.orderLines} />
          <InvoiceHistoryTable subscriptionId={subscription.id} />
        </div>

        {/* Right column */}
        <div className="space-y-6">
          <TimelineCard subscriptionId={subscription.id} />
          <ChurnRiskCard customerId={subscription.customerId} />
          <DunningCard subscriptionId={subscription.id} />
        </div>
      </div>

      {/* Transition confirmation */}
      {confirmTransition && (
        <ConfirmModal
          open
          onClose={() => setConfirmTransition(null)}
          onConfirm={handleTransition}
          title={confirmTransition.label}
          message={`This will transition the subscription to "${confirmTransition.to}". This action may not be reversible.`}
          confirmLabel="Confirm"
          variant={confirmTransition.variant}
          loading={transitionMutation.isPending}
        />
      )}

      {/* Upgrade / Downgrade modals */}
      {upgradeOpen && (
        <UpgradeModal
          subscription={subscription}
          onClose={() => setUpgradeOpen(false)}
        />
      )}
      {downgradeOpen && (
        <DowngradeModal
          subscription={subscription}
          onClose={() => setDowngradeOpen(false)}
        />
      )}
    </div>
  );
};
