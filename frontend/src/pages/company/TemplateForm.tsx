import React from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Plus, X } from 'lucide-react';
import { templateSchema, type TemplateSchemaType } from '@/lib/companyValidations';
import type { Template } from '@/types/company';
import { useCreateTemplate, useUpdateTemplate } from '@/hooks/useTemplates';
import { useActivePlans } from '@/hooks/usePlans';
import { useProducts } from '@/hooks/useProducts';
import { Modal, Button, FormField, Input, Select } from '@/components/ui';

interface TemplateFormProps {
  open: boolean;
  onClose: () => void;
  template?: Template | null;
}

export const TemplateForm: React.FC<TemplateFormProps> = ({
  open,
  onClose,
  template,
}) => {
  const isEdit = !!template;
  const createM = useCreateTemplate();
  const updateM = useUpdateTemplate();
  const isPending = createM.isPending || updateM.isPending;

  const { data: plansData } = useActivePlans();
  const { data: productsData } = useProducts(1, 100);

  const planOptions = (plansData?.data ?? []).map((p) => ({
    label: p.name,
    value: p.id,
  }));

  const productOptions = (productsData?.data ?? []).map((p) => ({
    label: p.name,
    value: p.id,
  }));

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TemplateSchemaType>({
    resolver: zodResolver(templateSchema),
    defaultValues: template
      ? {
          name: template.name,
          validity_days: template.validity_days,
          plan_id: template.plan_id,
          product_lines: template.product_lines.map((pl) => ({
            product_id: pl.product_id,
            quantity: pl.quantity,
          })),
        }
      : {
          name: '',
          validity_days: 30,
          plan_id: '',
          product_lines: [],
        },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'product_lines',
  });

  const onSubmit = async (data: TemplateSchemaType) => {
    if (isEdit && template) {
      await updateM.mutateAsync({ id: template.id, body: data });
    } else {
      await createM.mutateAsync(data);
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
      title={isEdit ? 'Edit template' : 'New template'}
      size="lg"
      footer={
        <>
          <Button variant="ghost" onClick={handleClose} disabled={isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit(onSubmit)} loading={isPending}>
            {isEdit ? 'Save changes' : 'Create template'}
          </Button>
        </>
      }
    >
      <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormField label="Template name" name="name" required error={errors.name?.message}>
            <Input id="name" placeholder="e.g. Standard Quote" error={!!errors.name} {...register('name')} />
          </FormField>
          <FormField label="Validity (days)" name="validity_days" required error={errors.validity_days?.message}>
            <Input id="validity_days" type="number" min="1" error={!!errors.validity_days} {...register('validity_days')} />
          </FormField>
        </div>

        <FormField label="Plan" name="plan_id" required error={errors.plan_id?.message}>
          <Select
            id="plan_id"
            options={planOptions}
            placeholder="Select a plan"
            error={!!errors.plan_id}
            {...register('plan_id')}
          />
        </FormField>

        {/* Product lines */}
        <div className="border-t border-gray-800 pt-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-200">Product Lines</h3>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              icon={<Plus className="h-3.5 w-3.5" />}
              onClick={() => append({ product_id: '', quantity: 1 })}
            >
              Add line
            </Button>
          </div>

          {fields.length === 0 && (
            <p className="text-xs text-gray-500 text-center py-4">
              No product lines added yet.
            </p>
          )}

          <div className="space-y-3">
            {fields.map((f, idx) => (
              <div key={f.id} className="flex items-start gap-2">
                <div className="flex-1">
                  <Select
                    options={productOptions}
                    placeholder="Select product"
                    error={!!errors.product_lines?.[idx]?.product_id}
                    {...register(`product_lines.${idx}.product_id`)}
                  />
                </div>
                <div className="w-24">
                  <Input
                    type="number"
                    min="1"
                    placeholder="Qty"
                    error={!!errors.product_lines?.[idx]?.quantity}
                    {...register(`product_lines.${idx}.quantity`)}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => remove(idx)}
                  className="mt-1 h-9 w-9 flex items-center justify-center rounded-lg
                             text-gray-500 hover:text-red-400 hover:bg-red-500/10
                             transition-colors shrink-0"
                  aria-label="Remove line"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </form>
    </Modal>
  );
};
