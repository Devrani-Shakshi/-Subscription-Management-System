import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useSearchParams, Link, Navigate } from 'react-router-dom';
import { UserPlus } from 'lucide-react';
import { AxiosError } from 'axios';
import { useAuthStore } from '@/stores/authStore';
import { useRegister, useTenantBranding } from '@/hooks/useAuth';
import { registerSchema } from '@/lib/validations';
import { Button, FormField, Input } from '@/components/ui';
import {
  AuthLayout,
  PasswordInput,
  PasswordStrengthMeter,
  AuthErrorBanner,
} from '@/components/forms';
import type { RegisterFormData } from '@/lib/validations';
import type { AuthErrorResponse, AuthPageState } from '@/types/auth';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tenantSlug = searchParams.get('tenant');

  const setAuth = useAuthStore((s) => s.setAuth);
  const { data: branding } = useTenantBranding(tenantSlug);
  const registerMutation = useRegister();

  const [pageState, setPageState] = useState<AuthPageState>('idle');
  const [bannerError, setBannerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setError,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: '', email: '', password: '', confirmPassword: '' },
  });

  const watchedPassword = watch('password');

  const onSubmit = useCallback(
    async (data: RegisterFormData) => {
      if (!tenantSlug) return;
      setBannerError(null);
      setPageState('loading');

      registerMutation.mutate(
        {
          name: data.name,
          email: data.email,
          password: data.password,
          tenantSlug,
        },
        {
          onSuccess: (result) => {
            setPageState('success');
            setAuth(result.user, result.accessToken, result.user.tenantId);
            navigate('/portal/plans', { replace: true });
          },
          onError: (error) => {
            setPageState('error');
            const axiosError = error as AxiosError<AuthErrorResponse>;

            if (!axiosError.response) {
              setBannerError('Connection error. Check your internet.');
              return;
            }

            if (axiosError.response.status === 409) {
              setError('email', {
                type: 'manual',
                message: 'Account exists. Log in instead.',
              });
              return;
            }

            setBannerError(
              axiosError.response.data?.message ||
                'Registration failed. Please try again.'
            );
          },
        }
      );
    },
    [tenantSlug, registerMutation, setAuth, navigate, setError]
  );

  // Tenant slug is required for registration
  if (!tenantSlug) {
    return <Navigate to="/login" replace />;
  }

  return (
    <AuthLayout
      branding={branding}
      title="Create your account"
      subtitle={`Join ${branding?.name || 'the platform'} to get started`}
      footer={
        <span>
          Already have an account?{' '}
          <Link
            to={`/login?tenant=${tenantSlug}`}
            className="text-violet-400 hover:text-violet-300 font-medium transition-colors"
          >
            Sign in
          </Link>
        </span>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {bannerError && <AuthErrorBanner message={bannerError} />}

        <FormField
          label="Full name"
          name="register-name"
          error={errors.name?.message}
          required
        >
          <Input
            id="register-name"
            type="text"
            placeholder="Jane Doe"
            autoComplete="name"
            error={!!errors.name}
            disabled={pageState === 'loading' || pageState === 'success'}
            {...register('name')}
          />
        </FormField>

        <FormField
          label="Email"
          name="register-email"
          error={
            errors.email?.message === 'Account exists. Log in instead.' ? (
              <span>
                Account exists.{' '}
                <Link
                  to={`/login?tenant=${tenantSlug}`}
                  className="text-violet-400 hover:text-violet-300 underline"
                >
                  Log in instead
                </Link>
              </span>
            ) : (
              errors.email?.message
            )
          }
          required
        >
          <Input
            id="register-email"
            type="email"
            placeholder="you@company.com"
            autoComplete="email"
            error={!!errors.email}
            disabled={pageState === 'loading' || pageState === 'success'}
            {...register('email')}
          />
        </FormField>

        <FormField
          label="Password"
          name="register-password"
          error={errors.password?.message}
          required
        >
          <PasswordInput
            id="register-password"
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
          name="register-confirmPassword"
          error={errors.confirmPassword?.message}
          required
        >
          <PasswordInput
            id="register-confirmPassword"
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
          icon={<UserPlus className="h-4 w-4" />}
          className="w-full"
        >
          {pageState === 'success' ? 'Redirecting…' : 'Create account'}
        </Button>
      </form>
    </AuthLayout>
  );
};
