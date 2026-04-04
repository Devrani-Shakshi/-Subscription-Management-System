import React, { useState } from 'react';
import { Check, TrendingUp } from 'lucide-react';
import { Modal, Button, PageLoader } from '@/components/ui';
import {
  usePlans,
  useProRataPreview,
  useUpgradeSubscription,
} from '@/hooks/useSubscriptions';
import { formatCurrency } from '@/lib/utils';
import type { Subscription, Plan } from '@/types/subscription';

interface UpgradeModalProps {
  subscription: Subscription;
  onClose: () => void;
}

export const UpgradeModal: React.FC<UpgradeModalProps> = ({
  subscription,
  onClose,
}) => {
  const { data: allPlans, isLoading: plansLoading } = usePlans();
  const upgradeMutation = useUpgradeSubscription();
  const [selectedPlanId, setSelectedPlanId] = useState('');

  const { data: preview, isLoading: previewLoading } = useProRataPreview(
    subscription.id,
    selectedPlanId
  );

  const higherPlans = allPlans?.filter(
    (p) => p.price > subscription.mrr && p.id !== subscription.planId
  );

  const handleUpgrade = async () => {
    await upgradeMutation.mutateAsync({
      id: subscription.id,
      planId: selectedPlanId,
    });
    onClose();
  };

  return (
    <Modal
      open
      onClose={onClose}
      title="Upgrade Plan"
      size="lg"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={upgradeMutation.isPending}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleUpgrade}
            disabled={!selectedPlanId || previewLoading}
            loading={upgradeMutation.isPending}
            icon={<TrendingUp className="h-4 w-4" />}
          >
            Confirm Upgrade
          </Button>
        </>
      }
    >
      {plansLoading ? (
        <PageLoader />
      ) : (
        <div className="space-y-6">
          <p className="text-sm text-gray-400">
            Current plan: <span className="text-gray-200 font-medium">{subscription.planName}</span>
            {' · '}
            <span className="text-emerald-400">{formatCurrency(subscription.mrr)}/mo</span>
          </p>

          {/* Plan grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {higherPlans?.map((plan) => (
              <UpgradePlanCard
                key={plan.id}
                plan={plan}
                selected={selectedPlanId === plan.id}
                onSelect={() => setSelectedPlanId(plan.id)}
              />
            ))}
          </div>

          {higherPlans?.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">
              No higher plans available.
            </p>
          )}

          {/* Pro-rata preview */}
          {selectedPlanId && (
            <div className="rounded-lg border border-violet-500/20 bg-violet-500/5 p-4 space-y-2">
              {previewLoading ? (
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <div className="h-4 w-4 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
                  Calculating pro-rata…
                </div>
              ) : preview ? (
                <>
                  <p className="text-sm text-gray-300">
                    Today's charge:{' '}
                    <span className="text-violet-400 font-bold">
                      {formatCurrency(preview.todaysCharge)}
                    </span>
                  </p>
                  <p className="text-xs text-gray-500">
                    Pro-rated for {preview.daysRemaining} days remaining in current billing period
                  </p>
                </>
              ) : null}
            </div>
          )}
        </div>
      )}
    </Modal>
  );
};

/* ── Plan Card ─────────────────────────────────────────────────── */

interface UpgradePlanCardProps {
  plan: Plan;
  selected: boolean;
  onSelect: () => void;
}

const UpgradePlanCard: React.FC<UpgradePlanCardProps> = ({
  plan,
  selected,
  onSelect,
}) => (
  <button
    type="button"
    onClick={onSelect}
    className={`
      text-left p-4 rounded-xl border transition-all duration-200
      ${selected
        ? 'bg-violet-600/10 border-violet-500/40 shadow-lg shadow-violet-500/10'
        : 'bg-gray-800/50 border-gray-800 hover:border-gray-700'
      }
    `.trim()}
  >
    <div className="flex items-start justify-between">
      <div>
        <h4 className="text-sm font-semibold text-gray-100">{plan.name}</h4>
        <p className="text-lg font-bold text-violet-400 mt-1">
          {formatCurrency(plan.price)}
          <span className="text-xs text-gray-500 font-normal">/{plan.period}</span>
        </p>
      </div>
      {selected && (
        <div className="h-6 w-6 rounded-full bg-violet-600 flex items-center justify-center">
          <Check className="h-3.5 w-3.5 text-white" />
        </div>
      )}
    </div>
  </button>
);
