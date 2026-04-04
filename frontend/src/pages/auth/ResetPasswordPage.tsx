import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { KeyRound } from 'lucide-react';
import { AxiosError } from 'axios';
import toast from 'react-hot-toast';
import { useResetPassword } from '@/hooks/useAuth';
import { resetPasswordSchema } from '@/lib/validations';
import { Button, FormField } from '@/components/ui';
import {
  AuthLayout,
  PasswordInput,
  PasswordStrengthMeter,
  AuthErrorBanner,
} from '@/components/forms';
import type { ResetPasswordFormData } from '@/lib/validations';
import type { AuthErrorResponse, AuthPageState } from '@/types/auth';

// ─── Expired token page ──────────────────────────────────────────
const TokenExpired: React.FC = () => (
  <div className="min-h-dvh flex items-center justify-center bg-gray-950 px-4">
    <div className="text-center max-w-md animate-fade-in">
      <div className="h-20 w-20 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto mb-6">
        <svg className="h-10 w-10 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-gray-50 mb-2">
        Link Expired
      </h1>
      <p className="text-gray-400 text-sm leading-relaxed">
        This password reset link has expired or is invalid. Please request a
        new one.
      </p>
    </div>
  </div>
);

export const ResetPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const resetMutation = useResetPassword();
  const [pageState, setPageState] = useState<AuthPageState>('idle');
  const [bannerError, setBannerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { password: '', confirmPassword: '' },
  });

  const watchedPassword = watch('password');

  const onSubmit = useCallback(
    async (data: ResetPasswordFormData) => {
      if (!token) return;
      setBannerError(null);
      setPageState('loading');

      resetMutation.mutate(
        { token, password: data.password },
        {
          onSuccess: () => {
            setPageState('success');
            toast.success('Password updated. Please log in.');
            navigate('/login', { replace: true });
          },
          onError: (error) => {
            setPageState('error');
            const axiosError = error as AxiosError<AuthErrorResponse>;

            if (axiosError.response?.status === 410) {
              setBannerError(
                'This reset link has expired. Please request a new one.'
              );
              return;
            }

            setBannerError(
              axiosError.response?.data?.message ||
                'Failed to reset password. Please try again.'
            );
          },
        }
      );
    },
    [token, resetMutation, navigate]
  );

  if (!token) return <TokenExpired />;

  return (
    <AuthLayout
      title="Set new password"
      subtitle="Choose a strong password for your account"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {bannerError && <AuthErrorBanner message={bannerError} />}

        <FormField
          label="New password"
          name="reset-password"
          error={errors.password?.message}
          required
        >
          <PasswordInput
            id="reset-password"
            placeholder="••••••••"
            autoComplete="new-password"
            error={!!errors.password}
            disabled={pageState === 'loading' || pageState === 'success'}
            {...register('password')}
          />
          <PasswordStrengthMeter password={watchedPassword} />
        </FormField>

        <FormField
          label="Confirm new password"
          name="reset-confirmPassword"
          error={errors.confirmPassword?.message}
          required
        >
          <PasswordInput
            id="reset-confirmPassword"
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
          icon={<KeyRound className="h-4 w-4" />}
          className="w-full"
        >
          {pageState === 'success' ? 'Redirecting…' : 'Reset password'}
        </Button>
      </form>
    </AuthLayout>
  );
};
