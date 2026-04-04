import React, { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { useWizard } from '@/hooks/useWizard';
import { useCreateSubscription } from '@/hooks/useSubscriptions';
import { WizardProgress } from './subscriptions/wizard/WizardProgress';
import { StepCustomer } from './subscriptions/wizard/StepCustomer';
import { StepPlan } from './subscriptions/wizard/StepPlan';
import { StepProducts } from './subscriptions/wizard/StepProducts';
import { StepConfigure } from './subscriptions/wizard/StepConfigure';
import { StepReview } from './subscriptions/wizard/StepReview';
import { Button } from '@/components/ui';
import { ArrowLeft, ArrowRight, X } from 'lucide-react';
import type { WizardFormData } from '@/types/subscription';

const STEPS = [
  { label: 'Customer', key: 'customer' },
  { label: 'Plan', key: 'plan' },
  { label: 'Products', key: 'products' },
  { label: 'Configure', key: 'configure' },
  { label: 'Review', key: 'review' },
];

const INITIAL_DATA: WizardFormData = {
  customerId: '',
  customerName: '',
  planId: '',
  planName: '',
  products: [],
  startDate: '',
  expiryDate: '',
  paymentTerms: 'net_30',
  notes: '',
};

export const CreateSubscriptionWizard: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();
  const createMutation = useCreateSubscription();

  const handleComplete = useCallback(
    async (data: WizardFormData) => {
      const result = await createMutation.mutateAsync({
        customerId: data.customerId,
        planId: data.planId,
        products: data.products,
        startDate: data.startDate,
        expiryDate: data.expiryDate,
        paymentTerms: data.paymentTerms,
        notes: data.notes,
      });
      navigate(`/company/subscriptions/${result.id}`);
    },
    [createMutation, navigate]
  );

  const wizard = useWizard<WizardFormData>({
    totalSteps: STEPS.length,
    initialData: INITIAL_DATA,
    onComplete: handleComplete,
  });

  const canProceed = useMemo(() => {
    switch (wizard.currentStep) {
      case 0: return !!wizard.formData.customerId;
      case 1: return !!wizard.formData.planId;
      case 2: return true;
      case 3: return !!wizard.formData.startDate && !!wizard.formData.expiryDate;
      case 4: return true;
      default: return false;
    }
  }, [wizard.currentStep, wizard.formData]);

  const stepComponent = useMemo(() => {
    switch (wizard.currentStep) {
      case 0:
        return <StepCustomer formData={wizard.formData} setData={wizard.setData} />;
      case 1:
        return <StepPlan formData={wizard.formData} setData={wizard.setData} />;
      case 2:
        return <StepProducts formData={wizard.formData} setData={wizard.setData} />;
      case 3:
        return <StepConfigure formData={wizard.formData} setData={wizard.setData} />;
      case 4:
        return <StepReview formData={wizard.formData} />;
      default:
        return null;
    }
  }, [wizard.currentStep, wizard.formData, wizard.setData]);

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Top bar */}
      <div className="sticky top-0 z-30 bg-gray-950/90 backdrop-blur-md border-b border-gray-800">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-100">New Subscription</h1>
          <button
            onClick={() => navigate('/company/subscriptions')}
            className="h-9 w-9 flex items-center justify-center rounded-lg
                       text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors"
            aria-label="Close wizard"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {isMobile ? (
          /* ── Mobile: Full-screen steps ── */
          <div className="space-y-6">
            <WizardProgress steps={STEPS} current={wizard.currentStep} />
            <div className="min-h-[60vh]">{stepComponent}</div>
          </div>
        ) : (
          /* ── Desktop: Sidebar + content ── */
          <div className="flex gap-8">
            <aside className="w-56 shrink-0">
              <nav className="space-y-1 sticky top-24">
                {STEPS.map((s, i) => (
                  <button
                    key={s.key}
                    onClick={() => i < wizard.currentStep && wizard.goToStep(i)}
                    disabled={i > wizard.currentStep}
                    className={`
                      w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm
                      transition-all duration-200
                      ${i === wizard.currentStep
                        ? 'bg-violet-600/10 text-violet-400 border border-violet-500/20'
                        : i < wizard.currentStep
                          ? 'text-gray-300 hover:bg-gray-800/50 cursor-pointer'
                          : 'text-gray-600 cursor-not-allowed'
                      }
                    `.trim()}
                  >
                    <span
                      className={`
                        h-7 w-7 flex items-center justify-center rounded-full text-xs font-bold
                        ${i === wizard.currentStep
                          ? 'bg-violet-600 text-white'
                          : i < wizard.currentStep
                            ? 'bg-emerald-600/20 text-emerald-400'
                            : 'bg-gray-800 text-gray-600'
                        }
                      `.trim()}
                    >
                      {i < wizard.currentStep ? '✓' : i + 1}
                    </span>
                    {s.label}
                  </button>
                ))}
              </nav>
            </aside>

            <main className="flex-1 min-w-0">
              {stepComponent}
            </main>
          </div>
        )}
      </div>

      {/* Bottom navigation bar */}
      <div className="sticky bottom-0 z-30 bg-gray-950/90 backdrop-blur-md border-t border-gray-800">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={wizard.isFirstStep ? () => navigate('/company/subscriptions') : wizard.back}
            icon={<ArrowLeft className="h-4 w-4" />}
          >
            {wizard.isFirstStep ? 'Cancel' : 'Back'}
          </Button>

          <div className="text-xs text-gray-500">
            Step {wizard.currentStep + 1} of {wizard.totalSteps}
          </div>

          <Button
            variant="primary"
            onClick={wizard.isLastStep ? () => handleComplete(wizard.formData) : wizard.next}
            disabled={!canProceed}
            loading={createMutation.isPending}
            icon={wizard.isLastStep ? undefined : <ArrowRight className="h-4 w-4" />}
          >
            {wizard.isLastStep ? 'Create subscription' : 'Next'}
          </Button>
        </div>
      </div>
    </div>
  );
};
