import React from 'react';
import { useForm, useFieldArray, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Plus, X, Eye } from 'lucide-react';
import { planSchema, type PlanSchemaType } from '@/lib/companyValidations';
import type { Plan } from '@/types/company';
import { useCreatePlan, useUpdatePlan } from '@/hooks/usePlans';
import {
  Modal, Button, FormField, Input, Select, ToggleSwitch,
} from '@/components/ui';

interface PlanFormProps {
  open: boolean;
  onClose: () => void;
  plan?: Plan | null;
}

const PERIOD_OPTIONS = [
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
  { label: 'Quarterly', value: 'quarterly' },
  { label: 'Yearly', value: 'yearly' },
];

export const PlanForm: React.FC<PlanFormProps> = ({ open, onClose, plan }) => {
  const isEdit = !!plan;
  const createM = useCreatePlan();
  const updateM = useUpdatePlan();
  const isPending = createM.isPending || updateM.isPending;
  const [preview, setPreview] = React.useState(false);

  const {
    register, control, handleSubmit, reset, watch,
    formState: { errors },
  } = useForm<PlanSchemaType>({
    resolver: zodResolver(planSchema),
    defaultValues: plan
      ? {
          name: plan.name,
          price: plan.price,
          billing_period: plan.billing_period,
          min_quantity: plan.min_quantity,
          start_date: plan.start_date?.split('T')[0] ?? '',
          end_date: plan.end_date?.split('T')[0] ?? '',
          auto_close: plan.auto_close,
          closable: plan.closable,
          pausable: plan.pausable,
          renewable: plan.renewable,
          features_json: plan.features_json ?? [],
        }
      : {
          name: '',
          price: 0,
          billing_period: 'monthly',
          min_quantity: 1,
          start_date: new Date().toISOString().split('T')[0],
          end_date: '',
          auto_close: false,
          closable: true,
          pausable: false,
          renewable: true,
          features_json: [],
        },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'features_json',
  });

  const watched = watch();

  const onSubmit = async (data: PlanSchemaType) => {
    const cleaned = {
      ...data,
      end_date: data.end_date || undefined,
    };
    if (isEdit && plan) {
      await updateM.mutateAsync({ id: plan.id, body: cleaned });
    } else {
      await createM.mutateAsync(cleaned);
    }
    reset();
    onClose();
  };

  const handleClose = () => { reset(); onClose(); };

  return (
    <>
      <Modal
        open={open}
        onClose={handleClose}
        title={isEdit ? 'Edit plan' : 'New plan'}
        size="xl"
        footer={
          <>
            <Button variant="ghost" onClick={handleClose} disabled={isPending}>
              Cancel
            </Button>
            <Button
              variant="secondary"
              icon={<Eye className="h-4 w-4" />}
              onClick={() => setPreview(true)}
            >
              Preview
            </Button>
            <Button onClick={handleSubmit(onSubmit)} loading={isPending}>
              {isEdit ? 'Save changes' : 'Create plan'}
            </Button>
          </>
        }
      >
        <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
          {/* Section 1 — Basic */}
          <div>
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Basic info</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Plan name" name="name" required error={errors.name?.message}>
                <Input id="name" placeholder="e.g. Pro Plan" error={!!errors.name} {...register('name')} />
              </FormField>
              <FormField label="Price" name="price" required error={errors.price?.message}>
                <Input id="price" type="number" step="0.01" min="0" error={!!errors.price} {...register('price')} />
              </FormField>
              <FormField label="Billing period" name="billing_period" required error={errors.billing_period?.message}>
                <Select id="billing_period" options={PERIOD_OPTIONS} error={!!errors.billing_period} {...register('billing_period')} />
              </FormField>
              <FormField label="Min quantity" name="min_quantity" required error={errors.min_quantity?.message}>
                <Input id="min_quantity" type="number" min="1" error={!!errors.min_quantity} {...register('min_quantity')} />
              </FormField>
              <FormField label="Start date" name="start_date" required error={errors.start_date?.message}>
                <Input id="start_date" type="date" error={!!errors.start_date} {...register('start_date')} />
              </FormField>
              <FormField label="End date" name="end_date" hint="Leave empty for no expiry" error={errors.end_date?.message}>
                <Input id="end_date" type="date" error={!!errors.end_date} {...register('end_date')} />
              </FormField>
            </div>
          </div>

          {/* Section 2 — Flags */}
          <div className="border-t border-gray-800 pt-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Plan flags</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Controller name="auto_close" control={control} render={({ field }) => (
                <ToggleSwitch checked={field.value} onChange={field.onChange}
                  label="Auto-close" description="Automatically close subscription at end date" />
              )} />
              <Controller name="closable" control={control} render={({ field }) => (
                <ToggleSwitch checked={field.value} onChange={field.onChange}
                  label="Closable" description="Customer can close the subscription" />
              )} />
              <Controller name="pausable" control={control} render={({ field }) => (
                <ToggleSwitch checked={field.value} onChange={field.onChange}
                  label="Pausable" description="Customer can pause and resume" />
              )} />
              <Controller name="renewable" control={control} render={({ field }) => (
                <ToggleSwitch checked={field.value} onChange={field.onChange}
                  label="Renewable" description="Subscription auto-renews each period" />
              )} />
            </div>
          </div>

          {/* Section 3 — Features */}
          <div className="border-t border-gray-800 pt-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-300">Features</h3>
              <Button type="button" variant="ghost" size="sm"
                icon={<Plus className="h-3.5 w-3.5" />}
                onClick={() => append({ key: '', value: '' })}
              >
                Add feature
              </Button>
            </div>
            {fields.length === 0 && (
              <p className="text-xs text-gray-500 text-center py-4">No features added yet.</p>
            )}
            <div className="space-y-2">
              {fields.map((f, idx) => (
                <div key={f.id} className="flex items-start gap-2">
                  <Input placeholder="Feature (e.g. Max users)" error={!!errors.features_json?.[idx]?.key}
                    {...register(`features_json.${idx}.key`)} className="flex-1" />
                  <Input placeholder="Value (e.g. 10)" error={!!errors.features_json?.[idx]?.value}
                    {...register(`features_json.${idx}.value`)} className="flex-1" />
                  <button type="button" onClick={() => remove(idx)}
                    className="mt-1 h-9 w-9 flex items-center justify-center rounded-lg
                               text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors shrink-0">
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </form>
      </Modal>

      {/* Plan Preview */}
      <PlanPreviewModal open={preview} onClose={() => setPreview(false)} data={watched} />
    </>
  );
};

/* ── Plan preview card ────────────────────────────────────── */
interface PlanPreviewModalProps {
  open: boolean;
  onClose: () => void;
  data: PlanSchemaType;
}

const PlanPreviewModal: React.FC<PlanPreviewModalProps> = ({ open, onClose, data }) => {
  return (
    <Modal open={open} onClose={onClose} title="Plan preview" size="sm">
      <div className="bg-gradient-to-br from-violet-600/10 to-teal-600/10 border border-gray-800 rounded-xl p-6 text-center">
        <h3 className="text-xl font-bold text-gray-50">{data.name || 'Untitled Plan'}</h3>
        <div className="mt-3">
          <span className="text-3xl font-extrabold text-violet-400">
            ${Number(data.price || 0).toFixed(2)}
          </span>
          <span className="text-gray-400 text-sm ml-1">/ {data.billing_period}</span>
        </div>
        {data.features_json.length > 0 && (
          <ul className="mt-5 space-y-2 text-left">
            {data.features_json.map((f, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-gray-300">
                <span className="h-1.5 w-1.5 rounded-full bg-violet-400 shrink-0" />
                <span className="font-medium">{f.key}:</span>
                <span className="text-gray-400">{f.value}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="mt-5 flex flex-wrap gap-2 justify-center">
          {data.renewable && <MicroBadge label="Auto-renew" />}
          {data.pausable && <MicroBadge label="Pausable" />}
          {data.closable && <MicroBadge label="Closable" />}
          {data.auto_close && <MicroBadge label="Auto-close" />}
        </div>
      </div>
    </Modal>
  );
};

const MicroBadge: React.FC<{ label: string }> = ({ label }) => (
  <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-medium
                   rounded-full bg-gray-800 text-gray-400 border border-gray-700">
    {label}
  </span>
);
