import React from 'react';
import { CreditCard, ArrowRight } from 'lucide-react';
import { StatusBadge, Button } from '@/components/ui';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { PortalSubscription } from '@/types/portal';

interface SubscriptionPlanCardProps {
  subscription: PortalSubscription;
  brandingColor: string;
  onChangePlan: () => void;
  onCancel: () => void;
  isMobile: boolean;
}

export const SubscriptionPlanCard: React.FC<SubscriptionPlanCardProps> = ({
  subscription,
  onChangePlan,
  onCancel,
  isMobile,
}) => {
  return (
    <div className="relative overflow-hidden rounded-xl border border-gray-800 bg-gradient-to-br from-gray-900 via-gray-900 to-amber-950/20">
      {/* Subtle glow */}
      <div className="absolute top-0 right-0 w-48 h-48 bg-amber-500/5 rounded-full blur-3xl" />

      <div className="relative p-5 sm:p-6">
        {/* Header row */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-5">
          <div>
            <h2 className={`font-bold text-gray-50 ${isMobile ? 'text-xl' : 'text-2xl'}`}>
              {subscription.planName}
            </h2>
            <div className="flex items-center gap-2 mt-2">
              <span className="px-2 py-0.5 bg-gray-800 text-gray-400 text-xs rounded-md capitalize">
                {subscription.billingPeriod}
              </span>
              <StatusBadge
                status={subscription.status}
                className={isMobile ? 'text-sm px-3 py-1' : ''}
              />
            </div>
          </div>

          {/* Price */}
          <div className="text-right">
            <p className="text-2xl font-extrabold text-gray-50">
              {formatCurrency(subscription.price)}
            </p>
            <p className="text-xs text-gray-500">per {subscription.billingPeriod}</p>
          </div>
        </div>

        {/* Next billing */}
        <div className="flex items-center gap-2 text-sm text-gray-400 mb-5">
          <CreditCard className="h-4 w-4" />
          <span>
            Next billing date:{' '}
            <span className="text-gray-200 font-medium">
              {formatDate(subscription.nextBillingDate)}
            </span>
          </span>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <Button
            variant="primary"
            size="md"
            onClick={onChangePlan}
            icon={<ArrowRight className="h-4 w-4" />}
          >
            Change plan
          </Button>
          <button
            onClick={onCancel}
            className="text-sm text-gray-500 hover:text-red-400 transition-colors underline underline-offset-2"
          >
            Cancel subscription
          </button>
        </div>
      </div>
    </div>
  );
};
