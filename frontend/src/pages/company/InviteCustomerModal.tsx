import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  inviteCustomerSchema,
  type InviteCustomerSchemaType,
} from '@/lib/companyValidations';
import { useInviteCustomer } from '@/hooks/useCustomers';
import { Modal, Button, FormField, Input } from '@/components/ui';

interface InviteCustomerModalProps {
  open: boolean;
  onClose: () => void;
}

export const InviteCustomerModal: React.FC<InviteCustomerModalProps> = ({
  open,
  onClose,
}) => {
  const inviteMutation = useInviteCustomer();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<InviteCustomerSchemaType>({
    resolver: zodResolver(inviteCustomerSchema),
    defaultValues: { email: '' },
  });

  const onSubmit = async (data: InviteCustomerSchemaType) => {
    await inviteMutation.mutateAsync(data);
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
      title="Invite customer"
      size="sm"
      footer={
        <>
          <Button variant="ghost" onClick={handleClose} disabled={inviteMutation.isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit(onSubmit)} loading={inviteMutation.isPending}>
            Send invite
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <FormField label="Email address" name="email" required error={errors.email?.message}>
          <Input
            id="email"
            type="email"
            placeholder="customer@example.com"
            error={!!errors.email}
            {...register('email')}
          />
        </FormField>
        <p className="text-xs text-gray-500">
          An invitation email will be sent to this address. The customer will be able
          to register and access the portal.
        </p>
      </form>
    </Modal>
  );
};
