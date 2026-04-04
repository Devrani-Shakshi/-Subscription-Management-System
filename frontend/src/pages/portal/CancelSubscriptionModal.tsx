import React, { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Modal, Button, Select } from '@/components/ui';
import { useCancelSubscription } from '@/hooks/usePortal';
import { formatDate } from '@/lib/utils';
import type { PortalSubscription, CancelStep } from '@/types/portal';

interface CancelSubscriptionModalProps {
  open: boolean;
  onClose: () => void;
  subscription: PortalSubscription;
}

const CANCEL_REASONS = [
  { label: 'Select a reason (optional)', value: '' },
  { label: 'Too expensive', value: 'too_expensive' },
  { label: 'Switching to another product', value: 'switching' },
  { label: 'Not using it enough', value: 'not_using' },
  { label: 'Missing features', value: 'missing_features' },
  { label: 'Technical issues', value: 'technical_issues' },
  { label: 'Other', value: 'other' },
];

export const CancelSubscriptionModal: React.FC<CancelSubscriptionModalProps> = ({
  open,
  onClose,
  subscription,
}) => {
  const [step, setStep] = useState<CancelStep>('consequences');
  const [reason, setReason] = useState('');
  const cancelMutation = useCancelSubscription();

  const handleClose = () => {
    setStep('consequences');
    setReason('');
    onClose();
  };

  const handleConfirm = () => {
    cancelMutation.mutate(
      {
        subscriptionId: subscription.id,
        payload: { reason: reason || undefined },
      },
      { onSuccess: handleClose }
    );
  };

  return (
    <Modal open={open} onClose={handleClose} title="Cancel Subscription" size="md">
      {step === 'consequences' && (
        <div className="space-y-5">
          {/* Warning icon */}
          <div className="flex justify-center">
            <div className="h-14 w-14 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
              <AlertTriangle className="h-7 w-7 text-red-400" />
            </div>
          </div>

          {/* Consequences */}
          <div className="space-y-3 text-center">
            <h3 className="text-base font-semibold text-gray-100">
              Are you sure you want to cancel?
            </h3>
            <p className="text-sm text-gray-400">
              If you cancel your <span className="text-gray-200 font-medium">{subscription.planName}</span> plan:
            </p>
          </div>

          <ul className="space-y-2 bg-red-500/5 border border-red-500/15 rounded-lg p-4">
            <li className="text-sm text-gray-300 flex items-start gap-2">
              <span className="text-red-400 mt-0.5">•</span>
              Your subscription will remain active until{' '}
              <span className="font-medium text-gray-100">
                {formatDate(subscription.expiryDate || subscription.nextBillingDate)}
              </span>
            </li>
            <li className="text-sm text-gray-300 flex items-start gap-2">
              <span className="text-red-400 mt-0.5">•</span>
              You will lose access to all plan features after the end date
            </li>
            <li className="text-sm text-gray-300 flex items-start gap-2">
              <span className="text-red-400 mt-0.5">•</span>
              No future invoices will be generated
            </li>
          </ul>

          <div className="flex flex-col-reverse sm:flex-row items-center gap-3 pt-2">
            <Button variant="primary" className="w-full sm:w-auto" onClick={handleClose}>
              Keep my subscription
            </Button>
            <Button
              variant="ghost"
              className="w-full sm:w-auto text-gray-400"
              onClick={() => setStep('reason')}
            >
              Cancel anyway
            </Button>
          </div>
        </div>
      )}

      {step === 'reason' && (
        <div className="space-y-5">
          <div className="space-y-2">
            <h3 className="text-base font-semibold text-gray-100">
              We&apos;re sorry to see you go
            </h3>
            <p className="text-sm text-gray-400">
              Would you mind telling us why you&apos;re cancelling?
            </p>
          </div>

          <Select
            options={CANCEL_REASONS}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />

          <div className="flex items-center gap-3 justify-end pt-2">
            <Button variant="ghost" onClick={() => setStep('consequences')} disabled={cancelMutation.isPending}>
              Back
            </Button>
            <Button
              variant="danger"
              onClick={handleConfirm}
              loading={cancelMutation.isPending}
            >
              Confirm cancellation
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
};
