import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { LogIn } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/lib/axios';
import { useAuthStore } from '@/stores/authStore';
import { Button, Input, FormField } from '@/components/ui';
import type { User } from '@/types';

const loginSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

interface LoginResponse {
  data: {
    user: User;
    accessToken: string;
  };
}

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      const response = await api.post<LoginResponse>('/auth/login', data);
      const { user, accessToken } = response.data.data;
      setAuth(user, accessToken, user.tenantId);
      toast.success(`Welcome back, ${user.name}!`);

      const routeMap: Record<string, string> = {
        super_admin: '/admin',
        company: '/company',
        portal_user: '/portal',
      };
      navigate(routeMap[user.role] || '/');
    } catch {
      toast.error('Invalid email or password');
    }
  };

  return (
    <div className="min-h-dvh flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="h-14 w-14 rounded-2xl bg-violet-500/20 border border-violet-500/30 flex items-center justify-center mx-auto mb-4">
            <span className="text-xl font-bold text-violet-400">S</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-50">Welcome back</h1>
          <p className="text-sm text-gray-400 mt-1">
            Sign in to your SubFlow account
          </p>
        </div>

        {/* Form card */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-2xl shadow-black/30">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <FormField
              label="Email"
              name="email"
              error={errors.email?.message}
              required
            >
              <Input
                id="email"
                type="email"
                placeholder="you@company.com"
                error={!!errors.email}
                {...register('email')}
              />
            </FormField>

            <FormField
              label="Password"
              name="password"
              error={errors.password?.message}
              required
            >
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                error={!!errors.password}
                {...register('password')}
              />
            </FormField>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={isSubmitting}
              icon={<LogIn className="h-4 w-4" />}
              className="w-full"
            >
              Sign in
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};
