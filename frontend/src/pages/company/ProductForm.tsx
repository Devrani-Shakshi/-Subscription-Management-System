import React from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Plus, X } from 'lucide-react';
import { productSchema, type ProductSchemaType } from '@/lib/companyValidations';
import type { Product } from '@/types/company';
import { useCreateProduct, useUpdateProduct } from '@/hooks/useProducts';
import { Modal, Button, FormField, Input, Select } from '@/components/ui';

interface ProductFormProps {
  open: boolean;
  onClose: () => void;
  product?: Product | null;
}

const TYPE_OPTIONS = [
  { label: 'Physical', value: 'physical' },
  { label: 'Digital', value: 'digital' },
  { label: 'Service', value: 'service' },
];

export const ProductForm: React.FC<ProductFormProps> = ({
  open,
  onClose,
  product,
}) => {
  const isEdit = !!product;
  const createMutation = useCreateProduct();
  const updateMutation = useUpdateProduct();
  const isPending = createMutation.isPending || updateMutation.isPending;

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProductSchemaType>({
    resolver: zodResolver(productSchema),
    defaultValues: product
      ? {
          name: product.name,
          type: product.type,
          sales_price: product.sales_price,
          cost_price: product.cost_price,
          variants: (product.variants ?? []).map((v) => ({
            attribute: v.attribute,
            value: v.value,
            extra_price: v.extra_price,
          })),
        }
      : {
          name: '',
          type: 'physical',
          sales_price: 0,
          cost_price: 0,
          variants: [],
        },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'variants',
  });

  const onSubmit = async (data: ProductSchemaType) => {
    if (isEdit && product) {
      await updateMutation.mutateAsync({ id: product.id, body: data });
    } else {
      await createMutation.mutateAsync(data);
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
      title={isEdit ? 'Edit product' : 'New product'}
      size="lg"
      footer={
        <>
          <Button variant="ghost" onClick={handleClose} disabled={isPending}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit(onSubmit)}
            loading={isPending}
          >
            {isEdit ? 'Save changes' : 'Create product'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Basic fields */}
        <FormField label="Product name" name="name" required error={errors.name?.message}>
          <Input id="name" placeholder="e.g. Premium Widget" error={!!errors.name} {...register('name')} />
        </FormField>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <FormField label="Type" name="type" required error={errors.type?.message}>
            <Select
              id="type"
              options={TYPE_OPTIONS}
              error={!!errors.type}
              {...register('type')}
            />
          </FormField>

          <FormField label="Sales price" name="sales_price" required error={errors.sales_price?.message}>
            <Input
              id="sales_price"
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              error={!!errors.sales_price}
              {...register('sales_price')}
            />
          </FormField>

          <FormField label="Cost price" name="cost_price" required error={errors.cost_price?.message}>
            <Input
              id="cost_price"
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              error={!!errors.cost_price}
              {...register('cost_price')}
            />
          </FormField>
        </div>

        {/* Variants section */}
        <div className="border-t border-gray-800 pt-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-200">Variants</h3>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              icon={<Plus className="h-3.5 w-3.5" />}
              onClick={() => append({ attribute: '', value: '', extra_price: 0 })}
            >
              Add variant
            </Button>
          </div>

          {fields.length === 0 && (
            <p className="text-xs text-gray-500 text-center py-4">
              No variants added yet.
            </p>
          )}

          <div className="space-y-3">
            {fields.map((field, index) => (
              <div key={field.id} className="flex items-start gap-2">
                <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <Input
                    placeholder="Attribute (e.g. Color)"
                    error={!!errors.variants?.[index]?.attribute}
                    {...register(`variants.${index}.attribute`)}
                  />
                  <Input
                    placeholder="Value (e.g. Red)"
                    error={!!errors.variants?.[index]?.value}
                    {...register(`variants.${index}.value`)}
                  />
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="Extra price"
                    error={!!errors.variants?.[index]?.extra_price}
                    {...register(`variants.${index}.extra_price`)}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => remove(index)}
                  className="mt-1 h-9 w-9 flex items-center justify-center rounded-lg
                             text-gray-500 hover:text-red-400 hover:bg-red-500/10
                             transition-colors shrink-0"
                  aria-label="Remove variant"
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
