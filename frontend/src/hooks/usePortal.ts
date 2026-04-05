import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '@/lib/axios';
import { useAuthStore } from '@/stores/authStore';
import type { ApiResponse } from '@/types';
import type {
  TenantBranding,
  PortalSubscription,
  PortalPlan,
  PortalInvoice,
  PortalInvoiceFilters,
  PortalPayment,
  PortalProRataPreview,
  PortalDowngradePreview,
  PortalPaymentPayload,
  PortalProfile,
  ChangePasswordPayload,
  ActiveSession,
  CancelSubscriptionPayload,
} from '@/types/portal';
import type { AxiosError } from 'axios';

interface ApiError {
  message: string;
}

/* ── Tenant Branding ─────────────────────────────── */

export function useTenantBranding(): TenantBranding {
  const user = useAuthStore((s) => s.user);
  const tenantId = useAuthStore((s) => s.tenantId);

  return {
    companyName: user?.name ?? 'Portal',
    logo: null,
    primaryColor: '#f59e0b', // amber-400 default
    slug: tenantId ?? '',
  };
}

/* ── My Subscription ─────────────────────────────── */

export function useMySubscription() {
  return useQuery({
    queryKey: ['portal', 'my-subscription'],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<PortalSubscription | null>>(
        '/portal/my-subscription'
      );
      return data.data;
    },
  });
}

/* ── Available Plans ─────────────────────────────── */

export function useAvailablePlans(tenantSlug?: string) {
  const isPublic = !!tenantSlug;
  return useQuery({
    queryKey: ['portal', 'plans', tenantSlug],
    queryFn: async () => {
      const url = isPublic
        ? `/public/plans?tenant=${tenantSlug}`
        : '/portal/plans';
      const { data } = await api.get<ApiResponse<PortalPlan[]>>(url);
      return data.data;
    },
  });
}

/* ── Pro-Rata Preview ────────────────────────────── */

export function usePortalProRataPreview(subscriptionId: string, planId: string) {
  return useQuery({
    queryKey: ['portal', 'pro-rata', subscriptionId, planId],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<PortalProRataPreview>>(
        `/portal/my-subscription/change-plan/preview`,
        { params: { plan_id: planId } }
      );
      return data.data;
    },
    enabled: !!subscriptionId && !!planId,
  });
}

/* ── Downgrade Preview ───────────────────────────── */

export function usePortalDowngradePreview(subscriptionId: string, planId: string) {
  return useQuery({
    queryKey: ['portal', 'downgrade-preview', subscriptionId, planId],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<PortalDowngradePreview>>(
        `/portal/my-subscription/change-plan/preview`,
        { params: { plan_id: planId } }
      );
      return data.data;
    },
    enabled: !!subscriptionId && !!planId,
  });
}

export function usePortalSubscribe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ planId }: { planId: string }) => {
      const { data } = await api.post<ApiResponse<PortalSubscription>>(
        '/portal/my-subscription/create',
        { plan_id: planId }
      );
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal', 'my-subscription'] });
      toast.success('Successfully subscribed to plan!');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Subscription failed');
    },
  });
}

/* ── Upgrade Subscription ────────────────────────── */

export function usePortalUpgrade() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ subscriptionId, planId }: { subscriptionId: string; planId: string }) => {
      const { data } = await api.post<ApiResponse<PortalSubscription>>(
        `/portal/my-subscription/change-plan`,
        { plan_id: planId }
      );
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal', 'my-subscription'] });
      toast.success('Plan upgraded successfully!');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to upgrade plan');
    },
  });
}

/* ── Downgrade Subscription ──────────────────────── */

export function usePortalDowngrade() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ subscriptionId, planId }: { subscriptionId: string; planId: string }) => {
      const { data } = await api.post<ApiResponse<PortalSubscription>>(
        `/portal/my-subscription/change-plan`,
        { plan_id: planId }
      );
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal', 'my-subscription'] });
      toast.success('Plan downgrade scheduled');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to downgrade plan');
    },
  });
}

/* ── Cancel Scheduled Downgrade ──────────────────── */

export function useCancelScheduledDowngrade() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (subscriptionId: string) => {
      await api.post(`/portal/subscriptions/${subscriptionId}/cancel-downgrade`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal', 'my-subscription'] });
      toast.success('Scheduled change cancelled');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to cancel scheduled change');
    },
  });
}

/* ── Cancel Subscription ─────────────────────────── */

export function useCancelSubscription() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      subscriptionId,
      payload,
    }: {
      subscriptionId: string;
      payload: CancelSubscriptionPayload;
    }) => {
      await api.post(`/portal/subscriptions/${subscriptionId}/cancel`, payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal', 'my-subscription'] });
      toast.success('Subscription cancelled');
    },
    onError: (err: AxiosError<ApiError>) => {
      if (err.response?.status === 409) {
        toast.error(
          err.response.data?.message ||
            'This plan cannot be cancelled early. Contact support.'
        );
      } else {
        toast.error(err.response?.data?.message || 'Cancellation failed');
      }
    },
  });
}

/* ── My Invoices ─────────────────────────────────── */

export function useMyInvoices(filters: PortalInvoiceFilters) {
  return useQuery({
    queryKey: ['portal', 'invoices', filters],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<PortalInvoice[]>>(
        '/portal/invoices',
        { params: filters }
      );
      return data;
    },
  });
}

export function useDownloadPortalInvoicePdf() {
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.get(`/portal/invoices/${id}/pdf`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data as BlobPart]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice-${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    },
    onSuccess: () => {
      toast.success('PDF downloaded successfully');
    },
    onError: () => {
      toast.error('Failed to download PDF');
    }
  });
}

/* ── My Payments ─────────────────────────────────── */

export function useMyPayments() {
  return useQuery({
    queryKey: ['portal', 'payments'],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<PortalPayment[]>>(
        '/portal/payments'
      );
      return data.data;
    },
  });
}

/* ── Portal Payment ──────────────────────────────── */

export function usePortalPayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PortalPaymentPayload) => {
      const { data } = await api.post<ApiResponse<{ success: boolean }>>(
        `/portal/invoices/${payload.invoiceId}/pay`,
        { method: 'card', payment_token: 'mock-token' }
      );
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal', 'invoices'] });
      qc.invalidateQueries({ queryKey: ['portal', 'payments'] });
      qc.invalidateQueries({ queryKey: ['portal', 'my-subscription'] });
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Payment failed. Please try again.');
    },
  });
}

/* ── Profile ─────────────────────────────────────── */

export function usePortalProfile() {
  return useQuery({
    queryKey: ['portal', 'profile'],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<PortalProfile>>(
        '/portal/profile'
      );
      return data.data;
    },
  });
}

export function useUpdateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PortalProfile) => {
      const { data } = await api.put<ApiResponse<PortalProfile>>(
        '/portal/profile',
        payload
      );
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal', 'profile'] });
      toast.success('Profile updated');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to update profile');
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (payload: ChangePasswordPayload) => {
      await api.post('/portal/profile/password', payload);
    },
    onSuccess: () => {
      toast.success('Password updated');
    },
    onError: (err: AxiosError<ApiError>) => {
      // 422 is handled by form field errors
      if (err.response?.status !== 422) {
        toast.error(err.response?.data?.message || 'Failed to update password');
      }
    },
  });
}

/* ── Sessions ────────────────────────────────────── */

export function useActiveSessions() {
  return useQuery({
    queryKey: ['portal', 'sessions'],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<ActiveSession[]>>(
        '/portal/sessions'
      );
      return data.data;
    },
  });
}

export function useRevokeSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (sessionId: string) => {
      await api.delete(`/portal/sessions/${sessionId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal', 'sessions'] });
      toast.success('Session revoked');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to revoke session');
    },
  });
}

export function useRevokeAllSessions() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post('/portal/sessions/revoke-all');
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal', 'sessions'] });
      toast.success('All other sessions revoked');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to revoke sessions');
    },
  });
}
