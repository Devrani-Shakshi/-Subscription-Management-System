import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Lock } from 'lucide-react';
import { Button, FormField, Input, PasswordStrengthMeter } from '@/components/ui';
import { useChangePassword } from '@/hooks/usePortal';
import { changePasswordSchema } from '@/lib/portalValidations';
import type { ChangePasswordFormData } from '@/lib/portalValidations';
import type { AxiosError } from 'axios';

export const ChangePasswordSection: React.FC = () => {
  const changePassword = useChangePassword();

  const {
    register,
    handleSubmit,
    watch,
    reset,
    setError,
    formState: { errors },
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: { currentPassword: '', newPassword: '', confirmPassword: '' },
  });

  const newPassword = watch('newPassword');

  const onSubmit = (data: ChangePasswordFormData) => {
    changePassword.mutate(data, {
      onSuccess: () => reset(),
      onError: (err: unknown) => {
        const axiosErr = err as AxiosError<{ errors?: Array<{ field: string; message: string }> }>;
        if (axiosErr.response?.status === 422) {
          const fieldErrors = axiosErr.response.data?.errors ?? [];
          fieldErrors.forEach((fe) => {
            if (fe.field === 'currentPassword') {
              setError('currentPassword', { message: fe.message });
            }
          });
        }
      },
    });
  };

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-800">
        <h3 className="text-sm font-semibold text-gray-200">Change Password</h3>
      </div>
      <form onSubmit={handleSubmit(onSubmit)} className="p-5 space-y-4">
        <FormField
          label="Current password"
          name="currentPassword"
          error={errors.currentPassword?.message}
          required
        >
          <Input
            id="currentPassword"
            type="password"
            {...register('currentPassword')}
            error={!!errors.currentPassword}
            autoComplete="current-password"
          />
        </FormField>

        <FormField
          label="New password"
          name="newPassword"
          error={errors.newPassword?.message}
          required
        >
          <Input
            id="newPassword"
            type="password"
            {...register('newPassword')}
            error={!!errors.newPassword}
            autoComplete="new-password"
          />
          <PasswordStrengthMeter password={newPassword} className="mt-2" />
        </FormField>

        <FormField
          label="Confirm new password"
          name="confirmPassword"
          error={errors.confirmPassword?.message}
          required
        >
          <Input
            id="confirmPassword"
            type="password"
            {...register('confirmPassword')}
            error={!!errors.confirmPassword}
            autoComplete="new-password"
          />
        </FormField>

        <div className="flex justify-end pt-2">
          <Button
            type="submit"
            variant="primary"
            loading={changePassword.isPending}
            icon={<Lock className="h-4 w-4" />}
          >
            Update password
          </Button>
        </div>
      </form>
    </div>
  );
};
