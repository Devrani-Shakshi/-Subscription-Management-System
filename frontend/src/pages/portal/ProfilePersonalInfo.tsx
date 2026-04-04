import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Save } from 'lucide-react';
import { Button, FormField, Input } from '@/components/ui';
import { useUpdateProfile } from '@/hooks/usePortal';
import { profileSchema } from '@/lib/portalValidations';
import type { ProfileFormData } from '@/lib/portalValidations';
import type { PortalProfile } from '@/types/portal';

interface PersonalInfoSectionProps {
  profile: PortalProfile;
}

export const PersonalInfoSection: React.FC<PersonalInfoSectionProps> = ({ profile }) => {
  const updateProfile = useUpdateProfile();

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: profile.name,
      email: profile.email,
      street: profile.street,
      city: profile.city,
      state: profile.state,
      country: profile.country,
      zip: profile.zip,
    },
  });

  const onSubmit = (data: ProfileFormData) => {
    updateProfile.mutate({
      name: data.name,
      email: profile.email,
      street: data.street ?? '',
      city: data.city ?? '',
      state: data.state ?? '',
      country: data.country ?? '',
      zip: data.zip ?? '',
    });
  };

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-800">
        <h3 className="text-sm font-semibold text-gray-200">Personal Information</h3>
      </div>
      <form onSubmit={handleSubmit(onSubmit)} className="p-5 space-y-4">
        <FormField label="Name" name="name" error={errors.name?.message} required>
          <Input id="name" {...register('name')} error={!!errors.name} />
        </FormField>

        <FormField
          label="Email"
          name="email"
          hint="Contact support to change your email address"
        >
          <Input id="email" value={profile.email} disabled />
        </FormField>

        <div className="pt-2">
          <p className="text-xs font-medium text-gray-400 mb-3">Billing Address</p>
          <div className="space-y-3">
            <FormField label="Street" name="street" error={errors.street?.message}>
              <Input id="street" {...register('street')} error={!!errors.street} />
            </FormField>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="City" name="city" error={errors.city?.message}>
                <Input id="city" {...register('city')} error={!!errors.city} />
              </FormField>
              <FormField label="State" name="state" error={errors.state?.message}>
                <Input id="state" {...register('state')} error={!!errors.state} />
              </FormField>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Country" name="country" error={errors.country?.message}>
                <Input id="country" {...register('country')} error={!!errors.country} />
              </FormField>
              <FormField label="ZIP" name="zip" error={errors.zip?.message}>
                <Input id="zip" {...register('zip')} error={!!errors.zip} />
              </FormField>
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button
            type="submit"
            variant="primary"
            loading={updateProfile.isPending}
            disabled={!isDirty}
            icon={<Save className="h-4 w-4" />}
          >
            Save changes
          </Button>
        </div>
      </form>
    </div>
  );
};
