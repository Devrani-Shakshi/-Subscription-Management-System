import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useParams } from 'react-router-dom';
import { UserCheck } from 'lucide-react';
import { AxiosError } from 'axios';
import { useAuthStore } from '@/stores/authStore';
import { useValidateInvite, useAcceptInvite } from '@/hooks/useAuth';
import { inviteAcceptSchema } from '@/lib/validations';
import { Button, FormField, Input } from '@/components/ui';
import {
  AuthLayout,
  PasswordInput,
  PasswordStrengthMeter,
  AuthErrorBanner,
} from '@/components/forms';
import type { InviteAcceptFormData } from '@/lib/validations';
import type { AuthErrorResponse, AuthPageState } from '@/types/auth';

const ROLE_ROUTES: Record<string, string> = {
  super_admin: '/admin/dashboard',
  company: '/company/dashboard',
  portal_user: '/portal/my-subscription',
};

// ─── Skeleton loader ──────────────────────────────────────────────
const InviteSkeleton: React.FC = () => (
  <div className="min-h-dvh flex items-center justify-center bg-gray-950 px-4">
    <div className="w-full max-w-md animate-pulse space-y-6">
      <div className="h-12 w-12 bg-gray-800 rounded-2xl mx-auto" />
      <div className="h-6 w-48 bg-gray-800 rounded mx-auto" />
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-5">
        <div className="h-4 w-full bg-gray-800 rounded" />
        <div className="h-10 w-full bg-gray-800 rounded-lg" />
        <div className="h-10 w-full bg-gray-800 rounded-lg" />
        <div className="h-10 w-full bg-gray-800 rounded-lg" />
        <div className="h-12 w-full bg-gray-800 rounded-lg" />
      </div>
    </div>
  </div>
);

// ─── Expired invite page ──────────────────────────────────────────
const InviteExpired: React.FC = () => (
  <div className="min-h-dvh flex items-center justify-center bg-gray-950 px-4">
    <div className="text-center max-w-md animate-fade-in">
      <div className="h-20 w-20 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto mb-6">
        <svg className="h-10 w-10 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-gray-50 mb-2">
        Invite Link Expired
      </h1>
      <p className="text-gray-400 text-sm leading-relaxed">
        This invite link has expired or has already been used. Contact the
        company to request a new invitation.
      </p>
    </div>
  </div>
);

export const InviteAcceptPage: React.FC = () => {
  const navigate = useNavigate();
  const { token = '' } = useParams<{ token: string }>();

  const { data: invite, isLoading, isError } = useValidateInvite(token);
  const acceptMutation = useAcceptInvite();

  const [pageState, setPageState] = useState<AuthPageState>('idle');
  const [bannerError, setBannerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<InviteAcceptFormData>({
    resolver: zodResolver(inviteAcceptSchema),
    defaultValues: { name: '', password: '', confirmPassword: '' },
  });

  const watchedPassword = watch('password');

  const onSubmit = useCallback(
    async (data: InviteAcceptFormData) => {
      setBannerError(null);
      setPageState('loading');

      acceptMutation.mutate(
        { token, name: data.name, password: data.password },
        {
          onSuccess: () => {
            setPageState('success');
            // Redirect to login — invite accept doesn't return tokens
            navigate('/login?accepted=1', { replace: true });
          },
          onError: (error) => {
            setPageState('error');
            const axiosError = error as AxiosError<AuthErrorResponse>;
            setBannerError(
              axiosError.response?.data?.message ||
                'Failed to accept invite. Please try again.'
            );
          },
        }
      );
    },
    [token, acceptMutation, navigate]
  );

  if (isLoading) return <InviteSkeleton />;
  if (isError || !invite) return <InviteExpired />;

  return (
    <AuthLayout
      title="Accept your invitation"
      subtitle={`You've been invited by ${invite.invitedBy} to join ${invite.companyName}`}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {bannerError && <AuthErrorBanner message={bannerError} />}

        {/* Invite info card */}
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-3 text-sm space-y-1">
          <div className="flex justify-between">
            <span className="text-gray-500">Email</span>
            <span className="text-gray-200">{invite.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Role</span>
            <span className="text-gray-200 capitalize">
              {invite.role.replace('_', ' ')}
            </span>
          </div>
        </div>

        <FormField
          label="Your name"
          name="invite-name"
          error={errors.name?.message}
          required
        >
          <Input
            id="invite-name"
            type="text"
            placeholder="Jane Doe"
            autoComplete="name"
            error={!!errors.name}
            disabled={pageState === 'loading' || pageState === 'success'}
            {...register('name')}
          />
        </FormField>

        <FormField
          label="Password"
          name="invite-password"
          error={errors.password?.message}
          required
        >
          <PasswordInput
            id="invite-password"
            placeholder="••••••••"
            autoComplete="new-password"
            error={!!errors.password}
            disabled={pageState === 'loading' || pageState === 'success'}
            {...register('password')}
          />
          <PasswordStrengthMeter password={watchedPassword} />
        </FormField>

        <FormField
          label="Confirm password"
          name="invite-confirmPassword"
          error={errors.confirmPassword?.message}
          required
        >
          <PasswordInput
            id="invite-confirmPassword"
            placeholder="••••••••"
            autoComplete="new-password"
            error={!!errors.confirmPassword}
            disabled={pageState === 'loading' || pageState === 'success'}
            {...register('confirmPassword')}
          />
        </FormField>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          loading={pageState === 'loading'}
          disabled={pageState === 'loading' || pageState === 'success'}
          icon={<UserCheck className="h-4 w-4" />}
          className="w-full"
        >
          {pageState === 'success' ? 'Redirecting…' : 'Accept & join'}
        </Button>
      </form>
    </AuthLayout>
  );
};
