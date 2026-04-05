import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { PageHeader, PageLoader, PageError, PlanCard } from '@/components/ui';
import { useAvailablePlans, useTenantBranding, useMySubscription, usePortalSubscribe } from '@/hooks/usePortal';
import { useAuthStore } from '@/stores/authStore';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { PlanSwitchModal } from './PlanSwitchModal';
import type { PortalPlan, PortalSubscription } from '@/types/portal';

export const PlansPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const user = useAuthStore((s) => s.user);
  const branding = useTenantBranding();
  const { isMobile, isTablet } = useBreakpoint();

  const tenantSlug = user ? undefined : (searchParams.get('tenant') ?? undefined);
  const { data: plans, isLoading, isError, refetch } = useAvailablePlans(tenantSlug);
  const { data: subscription } = useMySubscription();

  const [switchOpen, setSwitchOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<PortalPlan | null>(null);

  const subscribeMutation = usePortalSubscribe();

  const handleSelect = (plan: PortalPlan) => {
    if (!user) {
      const slug = tenantSlug || branding.slug;
      navigate(`/register?tenant=${slug}&plan=${plan.id}`);
      return;
    }
    
    // If they already have a subscription, open the Upgrade/Downgrade modal
    if (subscription) {
      setSelectedPlan(plan);
      setSwitchOpen(true);
      return;
    }

    // Otherwise create a new subscription directly
    subscribeMutation.mutate({ planId: plan.id }, {
      onSuccess: () => navigate('/portal')
    });
  };

  if (isLoading) return <PageLoader />;
  if (isError) return <PageError onRetry={refetch} />;

  const gridCols = isMobile
    ? 'grid-cols-1'
    : isTablet
    ? 'grid-cols-2'
    : 'grid-cols-3';

  return (
    <div className="space-y-6">
      {/* Unauthenticated header with company branding */}
      {!user && (
        <div className="text-center py-8 border-b border-gray-800 mb-6">
          <h1 className="text-3xl font-bold text-gray-50 mb-2">
            {branding.companyName}
          </h1>
          <p className="text-gray-400 text-sm">Choose a plan that fits your needs</p>
        </div>
      )}

      {user && (
        <PageHeader
          title="Available Plans"
          subtitle="Browse and compare our available subscription plans"
        />
      )}

      {/* Plan grid */}
      <div className={`grid ${gridCols} gap-5`}>
        {plans?.map((plan) => (
          <PlanCard
            key={plan.id}
            plan={plan}
            currentPlanId={subscription?.planId}
            currentPrice={subscription?.price}
            onSelect={handleSelect}
            showSelectButton
          />
        ))}
      </div>

      {/* Plan switch modal (only for authenticated users) */}
      {user && subscription && (
        <PlanSwitchModal
          open={switchOpen}
          onClose={() => {
            setSwitchOpen(false);
            setSelectedPlan(null);
          }}
          subscription={subscription}
        />
      )}
    </div>
  );
};
