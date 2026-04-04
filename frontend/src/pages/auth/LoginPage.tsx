import React, { useState, useEffect, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { LogIn } from 'lucide-react';
import { AxiosError } from 'axios';
import { useAuthStore } from '@/stores/authStore';
import { useLogin, useTenantBranding } from '@/hooks/useAuth';
import { loginSchema } from '@/lib/validations';
import { Button, FormField, Input } from '@/components/ui';
import {
  AuthLayout,
  PasswordInput,
  AuthErrorBanner,
} from '@/components/forms';
import type { LoginFormData } from '@/lib/validations';
import type { AuthErrorResponse, AuthPageState } from '@/types/auth';

const ROLE_ROUTES: Record<string, string> = {
  super_admin: '/admin/dashboard',
  company: '/company/dashboard',
  portal_user: '/portal/my-subscription',
};

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tenantSlug = searchParams.get('tenant');
  const redirectTo = searchParams.get('redirect');

  const setAuth = useAuthStore((s) => s.setAuth);
  const { data: branding } = useTenantBranding(tenantSlug);
  const loginMutation = useLogin();

  const [pageState, setPageState] = useState<AuthPageState>('idle');
  const [bannerError, setBannerError] = useState<string | null>(null);
  const [bannerVariant, setBannerVariant] = useState<
    'error' | 'warning' | 'network'
  >('error');
  const [retryCountdown, setRetryCountdown] = useState(0);
  const [isSuspended, setIsSuspended] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  // Countdown timer for rate-limiting
  useEffect(() => {
    if (retryCountdown <= 0) return;
    const timer = setInterval(() => {
      setRetryCountdown((prev) => {
        if (prev <= 1) {
          setBannerError(null);
          return 0;
        }
        setBannerError(`Too many attempts. Try again in ${prev - 1}s`);
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [retryCountdown]);

  const onSubmit = useCallback(
    async (data: LoginFormData) => {
      setBannerError(null);
      setPageState('loading');

      loginMutation.mutate(data, {
        onSuccess: (result) => {
          setPageState('success');
          setAuth(result.user, result.accessToken, result.user.tenantId);

          const target =
            redirectTo || ROLE_ROUTES[result.user.role] || '/';
          navigate(target, { replace: true });
        },
        onError: (error) => {
          setPageState('error');
          const axiosError = error as AxiosError<AuthErrorResponse>;

          if (!axiosError.response) {
            setBannerError('Connection error. Check your internet.');
            setBannerVariant('network');
            return;
          }

          const status = axiosError.response.status;

          switch (status) {
            case 401:
              setBannerError('Invalid email or password');
              setBannerVariant('error');
              break;
            case 429: {
              const retryAfter =
                axiosError.response.data?.retry_after || 30;
              setRetryCountdown(retryAfter);
              setBannerError(
                `Too many attempts. Try again in ${retryAfter}s`
              );
              setBannerVariant('warning');
              break;
            }
            case 403:
              setIsSuspended(true);
              break;
            default:
              setBannerError(
                axiosError.response.data?.message ||
                  'Something went wrong. Please try again.'
              );
              setBannerVariant('error');
          }
        },
      });
    },
    [loginMutation, navigate, redirectTo, setAuth]
  );

  // ─── Suspended full-page ────────────────────────────────────────
  if (isSuspended) {
    return (
      <div className="min-h-dvh flex items-center justify-center bg-gray-950 px-4">
        <div className="text-center max-w-md animate-fade-in">
          <div className="h-20 w-20 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-6">
            <svg className="h-10 w-10 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-50 mb-2">
            Access Unavailable
          </h1>
          <p className="text-gray-400 text-sm leading-relaxed mb-6">
            Your account has been suspended. Please contact your
            administrator or support team for assistance.
          </p>
          <Link
            to="/login"
            onClick={() => setIsSuspended(false)}
            className="text-sm text-violet-400 hover:text-violet-300 transition-colors"
          >
            ← Try a different account
          </Link>
        </div>
      </div>
    );
  }

  // ─── Main login UI ──────────────────────────────────────────────
  return (
    <AuthLayout
      branding={branding}
      title="Welcome back"
      subtitle="Sign in to your account to continue"
      footer={
        tenantSlug ? (
          <span>
            Don&apos;t have an account?{' '}
            <Link
              to={`/register?tenant=${tenantSlug}`}
              className="text-violet-400 hover:text-violet-300 font-medium transition-colors"
            >
              Sign up
            </Link>
          </span>
        ) : undefined
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Error banner */}
        {bannerError && (
          <AuthErrorBanner message={bannerError} variant={bannerVariant} />
        )}

        <FormField
          label="Email"
          name="login-email"
          error={errors.email?.message}
          required
        >
          <Input
            id="login-email"
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
          name="login-password"
          error={errors.password?.message}
          required
        >
          <PasswordInput
            id="login-password"
            placeholder="••••••••"
            autoComplete="current-password"
            error={!!errors.password}
            disabled={pageState === 'loading' || pageState === 'success'}
            {...register('password')}
          />
        </FormField>

        {/* Forgot password link */}
        <div className="flex justify-end">
          <Link
            to="/forgot-password"
            className="text-xs text-gray-500 hover:text-violet-400 transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          loading={pageState === 'loading'}
          disabled={
            retryCountdown > 0 ||
            pageState === 'loading' ||
            pageState === 'success'
          }
          icon={<LogIn className="h-4 w-4" />}
          className="w-full"
        >
          {pageState === 'success' ? 'Redirecting…' : 'Sign in'}
        </Button>
      </form>
    </AuthLayout>
  );
};
