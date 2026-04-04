import React, { useState } from 'react';
import { Check, TrendingDown, AlertTriangle } from 'lucide-react';
import { Modal, Button, PageLoader } from '@/components/ui';
import {
  usePlans,
  useDowngradePreview,
  useDowngradeSubscription,
} from '@/hooks/useSubscriptions';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Subscription, Plan } from '@/types/subscription';

interface DowngradeModalProps {
  subscription: Subscription;
  onClose: () => void;
}

export const DowngradeModal: React.FC<DowngradeModalProps> = ({
  subscription,
  onClose,
}) => {
  const { data: allPlans, isLoading: plansLoading } = usePlans();
  const downgradeMutation = useDowngradeSubscription();
  const [selectedPlanId, setSelectedPlanId] = useState('');

  const { data: preview, isLoading: previewLoading } = useDowngradePreview(
    subscription.id,
    selectedPlanId
  );

  const lowerPlans = allPlans?.filter(
    (p) => p.price < subscription.mrr && p.id !== subscription.planId
  );

  const handleDowngrade = async () => {
    await downgradeMutation.mutateAsync({
      id: subscription.id,
      planId: selectedPlanId,
    });
    onClose();
  };

  return (
    <Modal
      open
      onClose={onClose}
      title="Downgrade Plan"
      size="lg"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={downgradeMutation.isPending}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleDowngrade}
            disabled={!selectedPlanId || previewLoading}
            loading={downgradeMutation.isPending}
            icon={<TrendingDown className="h-4 w-4" />}
          >
            Confirm Downgrade
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
            {lowerPlans?.map((plan) => (
              <DowngradePlanCard
                key={plan.id}
                plan={plan}
                selected={selectedPlanId === plan.id}
                onSelect={() => setSelectedPlanId(plan.id)}
              />
            ))}
          </div>

          {lowerPlans?.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">
              No lower plans available.
            </p>
          )}

          {/* Downgrade preview */}
          {selectedPlanId && (
            <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4 space-y-3">
              {previewLoading ? (
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <div className="h-4 w-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                  Loading preview…
                </div>
              ) : preview ? (
                <>
                  <p className="text-sm text-gray-300">
                    Changes take effect on{' '}
                    <span className="text-amber-400 font-semibold">
                      {formatDate(preview.downgradeAt)}
                    </span>
                  </p>

                  {preview.warnings.length > 0 && (
                    <div className="space-y-2">
                      {preview.warnings.map((w, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                          <p className="text-xs text-amber-200">{w}</p>
                        </div>
                      ))}
                    </div>
                  )}
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

interface DowngradePlanCardProps {
  plan: Plan;
  selected: boolean;
  onSelect: () => void;
}

const DowngradePlanCard: React.FC<DowngradePlanCardProps> = ({
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
        ? 'bg-amber-600/10 border-amber-500/30 shadow-lg shadow-amber-500/10'
        : 'bg-gray-800/50 border-gray-800 hover:border-gray-700'
      }
    `.trim()}
  >
    <div className="flex items-start justify-between">
      <div>
        <h4 className="text-sm font-semibold text-gray-100">{plan.name}</h4>
        <p className="text-lg font-bold text-amber-400 mt-1">
          {formatCurrency(plan.price)}
          <span className="text-xs text-gray-500 font-normal">/{plan.period}</span>
        </p>
      </div>
      {selected && (
        <div className="h-6 w-6 rounded-full bg-amber-500 flex items-center justify-center">
          <Check className="h-3.5 w-3.5 text-white" />
        </div>
      )}
    </div>
  </button>
);
