import React, { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Modal, Button, PageLoader, PlanCard } from '@/components/ui';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import {
  useAvailablePlans,
  usePortalProRataPreview,
  usePortalDowngradePreview,
  usePortalUpgrade,
  usePortalDowngrade,
  useCancelScheduledDowngrade,
} from '@/hooks/usePortal';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { PortalSubscription, PortalPlan } from '@/types/portal';

type Step = 'browse' | 'upgrade-confirm' | 'downgrade-confirm';

interface PlanSwitchModalProps {
  open: boolean;
  onClose: () => void;
  subscription: PortalSubscription;
}

export const PlanSwitchModal: React.FC<PlanSwitchModalProps> = ({
  open,
  onClose,
  subscription,
}) => {
  const { isMobile } = useBreakpoint();
  const [step, setStep] = useState<Step>('browse');
  const [selectedPlan, setSelectedPlan] = useState<PortalPlan | null>(null);

  const { data: plans, isLoading: plansLoading } = useAvailablePlans();
  const upgradeMutation = usePortalUpgrade();
  const downgradeMutation = usePortalDowngrade();
  const cancelDowngrade = useCancelScheduledDowngrade();

  const handleClose = () => {
    setStep('browse');
    setSelectedPlan(null);
    onClose();
  };

  const handleSelect = (plan: PortalPlan) => {
    setSelectedPlan(plan);
    if (plan.price > subscription.price) {
      setStep('upgrade-confirm');
    } else {
      setStep('downgrade-confirm');
    }
  };

  const handleBack = () => {
    setStep('browse');
    setSelectedPlan(null);
  };

  const renderBrowse = () => {
    if (plansLoading) return <PageLoader />;
    if (!plans?.length) return <p className="text-gray-500 text-sm">No plans available.</p>;

    return (
      <div className="space-y-4">
        {/* Scheduled downgrade banner */}
        {subscription.scheduledDowngrade && (
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <p className="text-sm text-amber-300">
              Plan change to{' '}
              <span className="font-semibold">{subscription.scheduledDowngrade.planName}</span>{' '}
              scheduled for {formatDate(subscription.scheduledDowngrade.effectiveDate)}.
            </p>
            <button
              onClick={() => cancelDowngrade.mutate(subscription.id)}
              disabled={cancelDowngrade.isPending}
              className="text-sm text-amber-400 hover:text-amber-300 underline underline-offset-2 transition-colors"
            >
              {cancelDowngrade.isPending ? 'Cancelling...' : 'Cancel scheduled change'}
            </button>
          </div>
        )}

        <div className={`grid gap-4 ${isMobile ? 'grid-cols-1' : 'grid-cols-2'}`}>
          {plans.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              currentPlanId={subscription.planId}
              currentPrice={subscription.price}
              onSelect={handleSelect}
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <Modal open={open} onClose={handleClose} title="Change Plan" size="lg">
      {step === 'browse' && renderBrowse()}
      {step === 'upgrade-confirm' && selectedPlan && (
        <UpgradeConfirmStep
          subscription={subscription}
          plan={selectedPlan}
          onBack={handleBack}
          onConfirm={() => {
            upgradeMutation.mutate(
              { subscriptionId: subscription.id, planId: selectedPlan.id },
              { onSuccess: handleClose }
            );
          }}
          isLoading={upgradeMutation.isPending}
        />
      )}
      {step === 'downgrade-confirm' && selectedPlan && (
        <DowngradeConfirmStep
          subscription={subscription}
          plan={selectedPlan}
          onBack={handleBack}
          onConfirm={() => {
            downgradeMutation.mutate(
              { subscriptionId: subscription.id, planId: selectedPlan.id },
              { onSuccess: handleClose }
            );
          }}
          isLoading={downgradeMutation.isPending}
        />
      )}
    </Modal>
  );
};

/* ── Upgrade Confirm Step ────────────────────────── */

interface ConfirmStepProps {
  subscription: PortalSubscription;
  plan: PortalPlan;
  onBack: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

const UpgradeConfirmStep: React.FC<ConfirmStepProps> = ({
  subscription,
  plan,
  onBack,
  onConfirm,
  isLoading,
}) => {
  const { data: preview, isLoading: previewLoading } = usePortalProRataPreview(
    subscription.id,
    plan.id
  );

  if (previewLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-violet-400" />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="rounded-lg bg-gray-800/50 p-4 space-y-2">
        <h3 className="text-base font-semibold text-gray-100">
          Upgrade to {plan.name}
        </h3>
        {preview && (
          <>
            <p className="text-sm text-gray-300">
              Today you&apos;ll be charged{' '}
              <span className="font-bold text-emerald-400">
                {formatCurrency(preview.todaysCharge)}
              </span>{' '}
              (pro-rated for {preview.daysRemaining} remaining days).
            </p>
            <p className="text-xs text-gray-500">
              Effective {formatDate(preview.effectiveDate)}
            </p>
          </>
        )}
      </div>

      <div className="flex items-center gap-3 justify-end">
        <Button variant="ghost" onClick={onBack} disabled={isLoading}>
          Back
        </Button>
        <Button variant="primary" onClick={onConfirm} loading={isLoading}>
          Confirm upgrade
        </Button>
      </div>
    </div>
  );
};

/* ── Downgrade Confirm Step ──────────────────────── */

const DowngradeConfirmStep: React.FC<ConfirmStepProps> = ({
  subscription,
  plan,
  onBack,
  onConfirm,
  isLoading,
}) => {
  const { data: preview, isLoading: previewLoading } = usePortalDowngradePreview(
    subscription.id,
    plan.id
  );

  if (previewLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-amber-400" />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="rounded-lg bg-gray-800/50 p-4 space-y-3">
        <h3 className="text-base font-semibold text-gray-100">
          Downgrade to {plan.name}
        </h3>
        {preview && (
          <>
            <p className="text-sm text-gray-300">
              Your plan changes to{' '}
              <span className="font-semibold text-amber-400">{preview.newPlanName}</span>{' '}
              on{' '}
              <span className="font-semibold">{formatDate(preview.effectiveDate)}</span>.
            </p>
            {preview.warnings.length > 0 && (
              <div className="rounded-lg bg-amber-500/5 border border-amber-500/20 p-3">
                <p className="text-xs font-medium text-amber-400 mb-1">Please note:</p>
                <ul className="space-y-1">
                  {preview.warnings.map((w, i) => (
                    <li key={i} className="text-xs text-amber-300/80">• {w}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>

      <div className="flex items-center gap-3 justify-end">
        <Button variant="ghost" onClick={onBack} disabled={isLoading}>
          Back
        </Button>
        <Button variant="amber" onClick={onConfirm} loading={isLoading}>
          Confirm downgrade
        </Button>
      </div>
    </div>
  );
};
