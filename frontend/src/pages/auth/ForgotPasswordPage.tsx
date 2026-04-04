import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { forgotPasswordSchema } from '@/lib/validations';
import { useResetRequest } from '@/hooks/useAuth';
import { Button, FormField, Input } from '@/components/ui';
import { AuthLayout, AuthErrorBanner } from '@/components/forms';
import type { ForgotPasswordFormData } from '@/lib/validations';
import type { AuthPageState } from '@/types/auth';

export const ForgotPasswordPage: React.FC = () => {
  const resetRequestMutation = useResetRequest();
  const [pageState, setPageState] = useState<AuthPageState>('idle');
  const [submitted, setSubmitted] = useState(false);
  const [bannerError, setBannerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: '' },
  });

  const onSubmit = useCallback(
    async (data: ForgotPasswordFormData) => {
      setBannerError(null);
      setPageState('loading');

      resetRequestMutation.mutate(data, {
        onSuccess: () => {
          setPageState('success');
          setSubmitted(true);
        },
        onError: () => {
          // Always show the same message regardless of whether the email exists
          setPageState('success');
          setSubmitted(true);
        },
      });
    },
    [resetRequestMutation]
  );

  return (
    <AuthLayout
      title={submitted ? 'Check your email' : 'Forgot password?'}
      subtitle={
        submitted
          ? undefined
          : "No worries. Enter your email and we'll send you a reset link."
      }
      footer={
        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-gray-400 hover:text-gray-300 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to sign in
        </Link>
      }
    >
      {submitted ? (
        <div className="text-center py-4 animate-fade-in">
          <div className="h-14 w-14 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="h-7 w-7 text-green-400" />
          </div>
          <p className="text-sm text-gray-300 leading-relaxed">
            If an account exists with that email, a password reset link has
            been sent. Please check your inbox and spam folder.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 mt-6 text-sm text-violet-400 hover:text-violet-300 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to sign in
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {bannerError && <AuthErrorBanner message={bannerError} />}

          <FormField
            label="Email address"
            name="forgot-email"
            error={errors.email?.message}
            required
          >
            <Input
              id="forgot-email"
              type="email"
              placeholder="you@company.com"
              autoComplete="email"
              error={!!errors.email}
              disabled={pageState === 'loading'}
              {...register('email')}
            />
          </FormField>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            loading={pageState === 'loading'}
            disabled={pageState === 'loading'}
            icon={<Mail className="h-4 w-4" />}
            className="w-full"
          >
            Send reset link
          </Button>
        </form>
      )}
    </AuthLayout>
  );
};
