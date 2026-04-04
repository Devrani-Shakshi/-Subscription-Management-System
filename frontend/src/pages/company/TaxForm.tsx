import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { taxSchema, type TaxSchemaType } from '@/lib/companyValidations';
import type { Tax } from '@/types/company';
import { useCreateTax, useUpdateTax } from '@/hooks/useTaxes';
import { Modal, Button, FormField, Input } from '@/components/ui';

interface TaxFormProps {
  open: boolean;
  onClose: () => void;
  tax?: Tax | null;
}

export const TaxForm: React.FC<TaxFormProps> = ({ open, onClose, tax }) => {
  const isEdit = !!tax;
  const createM = useCreateTax();
  const updateM = useUpdateTax();
  const isPending = createM.isPending || updateM.isPending;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TaxSchemaType>({
    resolver: zodResolver(taxSchema),
    defaultValues: tax
      ? { name: tax.name, rate: tax.rate, type: tax.type }
      : { name: '', rate: 0, type: '' },
  });

  const onSubmit = async (data: TaxSchemaType) => {
    if (isEdit && tax) {
      await updateM.mutateAsync({ id: tax.id, body: data });
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
      title={isEdit ? 'Edit tax' : 'New tax'}
      size="sm"
      footer={
        <>
          <Button variant="ghost" onClick={handleClose} disabled={isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit(onSubmit)} loading={isPending}>
            {isEdit ? 'Save changes' : 'Create tax'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <FormField label="Tax name" name="name" required error={errors.name?.message}>
          <Input
            id="name"
            placeholder="e.g. GST"
            error={!!errors.name}
            {...register('name')}
          />
        </FormField>
        <FormField label="Rate (%)" name="rate" required error={errors.rate?.message}>
          <Input
            id="rate"
            type="number"
            step="0.01"
            min="0"
            max="100"
            placeholder="0 – 100"
            error={!!errors.rate}
            {...register('rate')}
          />
        </FormField>
        <FormField label="Type" name="type" required error={errors.type?.message}>
          <Input
            id="type"
            placeholder="e.g. VAT, Sales tax"
            error={!!errors.type}
            {...register('type')}
          />
        </FormField>
      </form>
    </Modal>
  );
};
