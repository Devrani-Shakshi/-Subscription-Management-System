import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/axios';
import type {
  TenantBrandingResponse,
  LoginRequest,
  AuthResponse,
  RegisterRequest,
  InviteAcceptRequest,
  InviteValidateResponse,
  ResetRequestPayload,
  ResetPasswordPayload,
} from '@/types/auth';

export function useTenantBranding(slug: string | null) {
  return useQuery({
    queryKey: ['tenant-branding', slug],
    queryFn: async () => {
      const response = await api.get<TenantBrandingResponse>(
        `/public/tenant/${slug}`
      );
      return response.data.data;
    },
    enabled: !!slug,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useLogin() {
  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      const response = await api.post('/auth/login', data);
      // Backend returns { access_token, role, tenant_id } directly
      const raw = response.data;

      // Decode the JWT payload to extract user info
      const payload = JSON.parse(atob(raw.access_token.split('.')[1]));

      return {
        user: {
          id: payload.sub,
          email: payload.email,
          name: payload.email.split('@')[0], // name not in JWT, fallback
          role: raw.role,
          tenantId: raw.tenant_id || null,
        },
        accessToken: raw.access_token,
      };
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: async (data: RegisterRequest) => {
      const response = await api.post<AuthResponse>('/auth/register', data);
      return response.data.data;
    },
  });
}

export function useValidateInvite(token: string) {
  return useQuery({
    queryKey: ['invite-validate', token],
    queryFn: async () => {
      const response = await api.get(
        `/auth/invite/validate/${token}`
      );
      // Backend returns { data: { email, invitedBy, role, companyName } }
      return response.data.data;
    },
    enabled: !!token,
    retry: false,
  });
}

export function useAcceptInvite() {
  return useMutation({
    mutationFn: async (data: InviteAcceptRequest) => {
      const response = await api.post(
        '/auth/invite/accept',
        data
      );
      return response.data;
    },
  });
}

export function useResetRequest() {
  return useMutation({
    mutationFn: async (data: ResetRequestPayload) => {
      await api.post('/auth/reset-request', data);
    },
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: async (data: ResetPasswordPayload) => {
      await api.post('/auth/reset-password', data);
    },
  });
}
