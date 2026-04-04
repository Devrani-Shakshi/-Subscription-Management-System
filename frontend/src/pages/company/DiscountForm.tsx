import React, { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { discountSchema, type DiscountSchemaType } from '@/lib/companyValidations';
import type { Discount } from '@/types/company';
import { useCreateDiscount, useUpdateDiscount } from '@/hooks/useDiscounts';
import { Modal, Button, FormField, Input, ToggleSwitch } from '@/components/ui';

interface DiscountFormProps {
  open: boolean;
  onClose: () => void;
  discount?: Discount | null;
}

export const DiscountForm: React.FC<DiscountFormProps> = ({
  open,
  onClose,
  discount,
}) => {
  const isEdit = !!discount;
  const createM = useCreateDiscount();
  const updateM = useUpdateDiscount();
  const isPending = createM.isPending || updateM.isPending;
  const [unlimited, setUnlimited] = useState(
    isEdit ? discount?.usage_limit === null : true
  );

  const {
    register,
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<DiscountSchemaType>({
    resolver: zodResolver(discountSchema),
    defaultValues: discount
      ? {
          name: discount.name,
          type: discount.type,
          value: discount.value,
          min_purchase: discount.min_purchase,
          min_quantity: discount.min_quantity,
          start_date: discount.start_date?.split('T')[0] ?? '',
          end_date: discount.end_date?.split('T')[0] ?? '',
          usage_limit: discount.usage_limit,
          applies_to: discount.applies_to,
        }
      : {
          name: '',
          type: 'percent',
          value: 0,
          min_purchase: 0,
          min_quantity: 0,
          start_date: new Date().toISOString().split('T')[0],
          end_date: '',
          usage_limit: null,
          applies_to: 'subscription',
        },
  });

  const discountType = watch('type');

  const onSubmit = async (data: DiscountSchemaType) => {
    const cleaned = {
      ...data,
      end_date: data.end_date || undefined,
      usage_limit: unlimited ? null : data.usage_limit,
    };
    if (isEdit && discount) {
      await updateM.mutateAsync({ id: discount.id, body: cleaned });
    } else {
      await createM.mutateAsync(cleaned);
    }
    reset();
    onClose();
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title={isEdit ? 'Edit discount' : 'New discount'}
      size="lg"
      footer={
        <>
          <Button variant="ghost" onClick={handleClose} disabled={isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit(onSubmit)} loading={isPending}>
            {isEdit ? 'Save changes' : 'Create discount'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <FormField label="Discount name" name="name" required error={errors.name?.message}>
          <Input id="name" placeholder="e.g. Summer Sale" error={!!errors.name} {...register('name')} />
        </FormField>

        {/* Type toggle */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Type</label>
          <div className="flex rounded-lg border border-gray-700 overflow-hidden">
            {(['fixed', 'percent'] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setValue('type', t)}
                className={`flex-1 h-10 text-sm font-medium transition-colors ${
                  discountType === t
                    ? 'bg-violet-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:text-gray-200'
                }`}
              >
                {t === 'fixed' ? 'Fixed ($)' : 'Percent (%)'}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormField label="Value" name="value" required error={errors.value?.message}>
            <Input
              id="value"
              type="number"
              step="0.01"
              min="0"
              placeholder={discountType === 'percent' ? '0 – 100' : '0.00'}
              error={!!errors.value}
              {...register('value')}
            />
          </FormField>
          <FormField label="Min purchase" name="min_purchase" error={errors.min_purchase?.message}>
            <Input id="min_purchase" type="number" step="0.01" min="0" error={!!errors.min_purchase} {...register('min_purchase')} />
          </FormField>
          <FormField label="Min quantity" name="min_quantity" error={errors.min_quantity?.message}>
            <Input id="min_quantity" type="number" min="0" error={!!errors.min_quantity} {...register('min_quantity')} />
          </FormField>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormField label="Start date" name="start_date" required error={errors.start_date?.message}>
            <Input id="start_date" type="date" error={!!errors.start_date} {...register('start_date')} />
          </FormField>
          <FormField label="End date" name="end_date" hint="Leave empty for no expiry" error={errors.end_date?.message}>
            <Input id="end_date" type="date" error={!!errors.end_date} {...register('end_date')} />
          </FormField>
        </div>

        {/* Usage limit */}
        <div className="space-y-3">
          <ToggleSwitch
            checked={unlimited}
            onChange={(val) => {
              setUnlimited(val);
              if (val) setValue('usage_limit', null);
            }}
            label="Unlimited usage"
            description="No limit on how many times this discount can be used"
          />
          {!unlimited && (
            <FormField label="Usage limit" name="usage_limit" error={errors.usage_limit?.message}>
              <Input
                id="usage_limit"
                type="number"
                min="1"
                placeholder="e.g. 100"
                error={!!errors.usage_limit}
                {...register('usage_limit')}
              />
            </FormField>
          )}
        </div>

        {/* Applies to */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Applies to</label>
          <div className="flex gap-4">
            {(['product', 'subscription'] as const).map((opt) => (
              <label key={opt} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  value={opt}
                  {...register('applies_to')}
                  className="h-4 w-4 text-violet-600 bg-gray-800 border-gray-600 focus:ring-violet-500"
                />
                <span className="text-sm text-gray-300 capitalize">{opt}</span>
              </label>
            ))}
          </div>
        </div>
      </form>
    </Modal>
  );
};
