import React from 'react';
import { Check, Star } from 'lucide-react';
import { Button, StatusBadge } from '@/components/ui';
import { formatCurrency } from '@/lib/utils';
import type { PortalPlan } from '@/types/portal';

interface PlanCardProps {
  plan: PortalPlan;
  currentPlanId?: string;
  onSelect?: (plan: PortalPlan) => void;
  showSelectButton?: boolean;
  currentPrice?: number;
  className?: string;
}

export const PlanCard: React.FC<PlanCardProps> = ({
  plan,
  currentPlanId,
  onSelect,
  showSelectButton = true,
  currentPrice,
  className = '',
}) => {
  const isCurrent = currentPlanId === plan.id;
  const isUpgrade = currentPrice !== undefined && plan.price > currentPrice;
  const isDowngrade = currentPrice !== undefined && plan.price < currentPrice;

  const getButtonConfig = () => {
    if (isCurrent) return null;
    if (currentPrice === undefined || currentPlanId === undefined) return { label: 'Subscribe', variant: 'primary' as const };
    if (isUpgrade) return { label: 'Upgrade', variant: 'primary' as const };
    if (isDowngrade) return { label: 'Downgrade', variant: 'amber' as const };
    return { label: 'Switch to this plan', variant: 'primary' as const };
  };

  const buttonConfig = getButtonConfig();

  return (
    <div
      className={`
        relative bg-gray-900 border rounded-xl p-6
        transition-all duration-200 hover:border-gray-600
        ${plan.popular ? 'border-amber-500/40 shadow-lg shadow-amber-500/5' : 'border-gray-800'}
        ${isCurrent ? 'ring-2 ring-violet-500/30' : ''}
        ${className}
      `.trim()}
    >
      {/* Popular badge */}
      {plan.popular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="inline-flex items-center gap-1 px-3 py-1 bg-amber-500 text-gray-950 text-xs font-bold rounded-full">
            <Star className="h-3 w-3" />
            Most popular
          </span>
        </div>
      )}

      {/* Current plan badge */}
      {isCurrent && (
        <div className="absolute -top-3 right-4">
          <StatusBadge status="active" className="text-xs" />
        </div>
      )}

      {/* Plan name + billing period */}
      <div className="mb-4">
        <h3 className="text-lg font-bold text-gray-100">{plan.name}</h3>
        <span className="inline-block mt-1 px-2 py-0.5 bg-gray-800 text-gray-400 text-xs rounded-md capitalize">
          {plan.billingPeriod}
        </span>
      </div>

      {/* Price */}
      <div className="mb-6">
        <span className="text-3xl font-extrabold text-gray-50">
          {formatCurrency(plan.price)}
        </span>
        <span className="text-sm text-gray-500 ml-1">
          /{plan.billingPeriod}
        </span>
      </div>

      {/* Features */}
      <ul className="space-y-2.5 mb-6">
        {plan.features.map((feature, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
            <Check className="h-4 w-4 text-emerald-400 mt-0.5 shrink-0" />
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      {/* Action */}
      {showSelectButton && (
        <div className="mt-auto">
          {isCurrent ? (
            <div className="w-full h-11 flex items-center justify-center rounded-lg bg-gray-800 border border-gray-700 text-gray-400 text-sm font-medium">
              Current plan
            </div>
          ) : buttonConfig && onSelect ? (
            <Button
              variant={buttonConfig.variant}
              size="lg"
              className="w-full"
              onClick={() => onSelect(plan)}
            >
              {buttonConfig.label}
            </Button>
          ) : null}
        </div>
      )}
    </div>
  );
};
