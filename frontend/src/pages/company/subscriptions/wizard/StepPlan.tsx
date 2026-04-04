import React, { useState } from 'react';
import { Check, Layers } from 'lucide-react';
import { PageLoader, Select } from '@/components/ui';
import { usePlans, useQuotationTemplates } from '@/hooks/useSubscriptions';
import { formatCurrency } from '@/lib/utils';
import type { WizardFormData, Plan } from '@/types/subscription';

interface StepPlanProps {
  formData: WizardFormData;
  setData: (data: Partial<WizardFormData>) => void;
}

export const StepPlan: React.FC<StepPlanProps> = ({ formData, setData }) => {
  const { data: plans, isLoading } = usePlans();
  const { data: templates } = useQuotationTemplates();
  const [templateId, setTemplateId] = useState('');

  const handleSelectPlan = (plan: Plan) => {
    setData({ planId: plan.id, planName: plan.name });
  };

  const handleApplyTemplate = (id: string) => {
    setTemplateId(id);
    const tmpl = templates?.find((t) => t.id === id);
    if (tmpl) {
      setData({
        planId: tmpl.planId,
        planName: plans?.find((p) => p.id === tmpl.planId)?.name ?? '',
        products: tmpl.products,
      });
    }
  };

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-semibold text-gray-100">Select Plan</h2>
          <p className="mt-1 text-sm text-gray-400">
            Choose a subscription plan for this customer.
          </p>
        </div>

        {templates && templates.length > 0 && (
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-gray-400" />
            <Select
              value={templateId}
              onChange={(e) => handleApplyTemplate(e.target.value)}
              options={templates.map((t) => ({ label: t.name, value: t.id }))}
              placeholder="Apply template"
            />
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {plans?.map((plan) => (
          <PlanCard
            key={plan.id}
            plan={plan}
            selected={formData.planId === plan.id}
            onSelect={() => handleSelectPlan(plan)}
          />
        ))}
      </div>
    </div>
  );
};

/* ── Plan Card ─────────────────────────────────────────────────── */

interface PlanCardProps {
  plan: Plan;
  selected: boolean;
  onSelect: () => void;
}

const PlanCard: React.FC<PlanCardProps> = ({ plan, selected, onSelect }) => (
  <button
    type="button"
    onClick={onSelect}
    className={`
      relative text-left p-5 rounded-xl border transition-all duration-200
      ${selected
        ? 'bg-violet-600/10 border-violet-500/40 shadow-lg shadow-violet-500/10'
        : 'bg-gray-900 border-gray-800 hover:border-gray-700 hover:bg-gray-800/30'
      }
    `.trim()}
  >
    {selected && (
      <div className="absolute top-3 right-3 h-6 w-6 rounded-full bg-violet-600
                      flex items-center justify-center animate-scale-in">
        <Check className="h-3.5 w-3.5 text-white" />
      </div>
    )}

    <h3 className="text-lg font-semibold text-gray-100">{plan.name}</h3>

    <div className="mt-2 flex items-baseline gap-1">
      <span className="text-2xl font-bold text-violet-400">
        {formatCurrency(plan.price)}
      </span>
      <span className="text-sm text-gray-500">/{plan.period}</span>
    </div>

    <ul className="mt-4 space-y-2">
      {plan.features.slice(0, 5).map((feature, i) => (
        <li key={i} className="flex items-center gap-2 text-sm text-gray-400">
          <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
          {feature}
        </li>
      ))}
    </ul>
  </button>
);
