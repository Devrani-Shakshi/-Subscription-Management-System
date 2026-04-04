import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/axios';
import toast from 'react-hot-toast';
import type { ApiResponse } from '@/types';
import type {
  Subscription,
  SubscriptionSummary,
  SubscriptionFilters,
  Customer,
  Plan,
  Product,
  QuotationTemplate,
  CreateSubscriptionPayload,
  TransitionPayload,
  ProRataPreview,
  DowngradePreview,
  InvoiceSummary,
  AuditTimelineEntry,
  ChurnRiskInfo,
  DunningInfo,
  BulkConflict,
  BulkJobStatus,
  BulkAction,
} from '@/types/subscription';

// ─── Subscriptions List ───────────────────────────────────────────
export function useSubscriptions(filters: SubscriptionFilters) {
  return useQuery({
    queryKey: ['company', 'subscriptions', filters],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        page: filters.page,
        limit: filters.limit,
      };
      if (filters.status) params.status = filters.status;
      if (filters.planId) params.planId = filters.planId;
      if (filters.search) params.search = filters.search;
      if (filters.startFrom) params.startFrom = filters.startFrom;
      if (filters.startTo) params.startTo = filters.startTo;
      if (filters.expiryFrom) params.expiryFrom = filters.expiryFrom;
      if (filters.expiryTo) params.expiryTo = filters.expiryTo;
      if (filters.sortBy) params.sortBy = filters.sortBy;
      if (filters.sortDir) params.sortDir = filters.sortDir;

      const res = await api.get<ApiResponse<SubscriptionSummary[]>>(
        '/company/subscriptions',
        { params }
      );
      return res.data;
    },
    staleTime: 30_000,
  });
}

// ─── Single Subscription ─────────────────────────────────────────
export function useSubscription(id: string) {
  return useQuery({
    queryKey: ['company', 'subscriptions', id],
    queryFn: async () => {
      const res = await api.get<ApiResponse<Subscription>>(
        `/company/subscriptions/${id}`
      );
      return res.data.data;
    },
    enabled: !!id,
  });
}

// ─── Customer Search ──────────────────────────────────────────────
export function useCustomerSearch(search: string) {
  return useQuery({
    queryKey: ['company', 'customers', 'search', search],
    queryFn: async () => {
      const res = await api.get<ApiResponse<Customer[]>>(
        '/company/customers',
        { params: { search } }
      );
      return res.data.data;
    },
    enabled: search.length >= 2,
    staleTime: 10_000,
  });
}

// ─── Plans ────────────────────────────────────────────────────────
export function usePlans() {
  return useQuery({
    queryKey: ['company', 'plans'],
    queryFn: async () => {
      const res = await api.get<ApiResponse<Plan[]>>('/company/plans');
      return res.data.data;
    },
    staleTime: 60_000,
  });
}

// ─── Product Search ───────────────────────────────────────────────
export function useProductSearch(search: string) {
  return useQuery({
    queryKey: ['company', 'products', 'search', search],
    queryFn: async () => {
      const res = await api.get<ApiResponse<Product[]>>(
        '/company/products',
        { params: { search } }
      );
      return res.data.data;
    },
    enabled: search.length >= 1,
    staleTime: 10_000,
  });
}

// ─── Quotation Templates ─────────────────────────────────────────
export function useQuotationTemplates() {
  return useQuery({
    queryKey: ['company', 'templates'],
    queryFn: async () => {
      const res = await api.get<ApiResponse<QuotationTemplate[]>>(
        '/company/templates'
      );
      return res.data.data;
    },
    staleTime: 60_000,
  });
}

// ─── Invoice History (for detail page) ────────────────────────────
export function useSubscriptionInvoices(subscriptionId: string) {
  return useQuery({
    queryKey: ['company', 'subscriptions', subscriptionId, 'invoices'],
    queryFn: async () => {
      const res = await api.get<ApiResponse<InvoiceSummary[]>>(
        `/company/subscriptions/${subscriptionId}/invoices`,
        { params: { limit: 5 } }
      );
      return res.data.data;
    },
    enabled: !!subscriptionId,
  });
}

// ─── Audit Timeline ──────────────────────────────────────────────
export function useSubscriptionTimeline(subscriptionId: string) {
  return useQuery({
    queryKey: ['company', 'subscriptions', subscriptionId, 'timeline'],
    queryFn: async () => {
      const res = await api.get<ApiResponse<AuditTimelineEntry[]>>(
        `/company/subscriptions/${subscriptionId}/timeline`
      );
      return res.data.data;
    },
    enabled: !!subscriptionId,
  });
}

// ─── Churn Risk ───────────────────────────────────────────────────
export function useChurnRisk(customerId: string) {
  return useQuery({
    queryKey: ['company', 'customers', customerId, 'churn'],
    queryFn: async () => {
      const res = await api.get<ApiResponse<ChurnRiskInfo>>(
        `/company/customers/${customerId}/churn`
      );
      return res.data.data;
    },
    enabled: !!customerId,
  });
}

// ─── Dunning Info ─────────────────────────────────────────────────
export function useDunningInfo(subscriptionId: string) {
  return useQuery({
    queryKey: ['company', 'subscriptions', subscriptionId, 'dunning'],
    queryFn: async () => {
      const res = await api.get<ApiResponse<DunningInfo>>(
        `/company/subscriptions/${subscriptionId}/dunning`
      );
      return res.data.data;
    },
    enabled: !!subscriptionId,
  });
}

// ─── Pro-rata Preview ─────────────────────────────────────────────
export function useProRataPreview(subscriptionId: string, planId: string) {
  return useQuery({
    queryKey: ['company', 'subscriptions', subscriptionId, 'pro-rata', planId],
    queryFn: async () => {
      const res = await api.get<ApiResponse<ProRataPreview>>(
        `/company/subscriptions/${subscriptionId}/change-plan/preview`,
        { params: { planId } }
      );
      return res.data.data;
    },
    enabled: !!subscriptionId && !!planId,
  });
}

// ─── Downgrade Preview ────────────────────────────────────────────
export function useDowngradePreview(subscriptionId: string, planId: string) {
  return useQuery({
    queryKey: ['company', 'subscriptions', subscriptionId, 'downgrade-preview', planId],
    queryFn: async () => {
      const res = await api.get<ApiResponse<DowngradePreview>>(
        `/company/subscriptions/${subscriptionId}/downgrade/preview`,
        { params: { planId } }
      );
      return res.data.data;
    },
    enabled: !!subscriptionId && !!planId,
  });
}

// ─── Bulk Conflicts ───────────────────────────────────────────────
export function useBulkConflicts(ids: string[], action: BulkAction) {
  return useQuery({
    queryKey: ['company', 'subscriptions', 'bulk', 'conflicts', ids, action],
    queryFn: async () => {
      const res = await api.get<ApiResponse<BulkConflict[]>>(
        '/company/subscriptions/bulk/conflicts',
        { params: { ids: ids.join(','), action } }
      );
      return res.data.data;
    },
    enabled: ids.length > 0,
  });
}

// ─── Bulk Job Status (polling) ────────────────────────────────────
export function useBulkJobStatus(jobId: string | null) {
  return useQuery({
    queryKey: ['company', 'bulk-jobs', jobId],
    queryFn: async () => {
      const res = await api.get<ApiResponse<BulkJobStatus>>(
        `/company/bulk-jobs/${jobId}`
      );
      return res.data.data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed') return false;
      return 2000;
    },
  });
}

// ─── Mutations ────────────────────────────────────────────────────
export function useCreateSubscription() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateSubscriptionPayload) => {
      const res = await api.post<ApiResponse<Subscription>>(
        '/company/subscriptions',
        data
      );
      return res.data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['company', 'subscriptions'] });
      toast.success('Subscription created successfully!');
    },
    onError: () => {
      toast.error('Failed to create subscription.');
    },
  });
}

export function useTransitionSubscription() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      payload,
    }: {
      id: string;
      payload: TransitionPayload;
    }) => {
      const res = await api.patch<ApiResponse<Subscription>>(
        `/company/subscriptions/${id}/transition`,
        payload
      );
      return res.data.data;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({
        queryKey: ['company', 'subscriptions', variables.id],
      });
      qc.invalidateQueries({ queryKey: ['company', 'subscriptions'] });
      toast.success(`Subscription transitioned to ${variables.payload.to}.`);
    },
    onError: (error: unknown) => {
      const axiosErr = error as { response?: { status?: number; data?: { message?: string } } };
      if (axiosErr.response?.status === 409) {
        toast.error(axiosErr.response.data?.message || 'Conflict: transition not allowed.');
      } else {
        toast.error('Transition failed.');
      }
    },
  });
}

export function useUpgradeSubscription() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, planId }: { id: string; planId: string }) => {
      const res = await api.post<ApiResponse<Subscription>>(
        `/company/subscriptions/${id}/upgrade`,
        { planId }
      );
      return res.data.data;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({
        queryKey: ['company', 'subscriptions', variables.id],
      });
      toast.success('Plan upgraded successfully!');
    },
    onError: () => {
      toast.error('Failed to upgrade plan.');
    },
  });
}

export function useDowngradeSubscription() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, planId }: { id: string; planId: string }) => {
      const res = await api.post<ApiResponse<Subscription>>(
        `/company/subscriptions/${id}/downgrade`,
        { planId }
      );
      return res.data.data;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({
        queryKey: ['company', 'subscriptions', variables.id],
      });
      toast.success('Plan downgrade scheduled.');
    },
    onError: () => {
      toast.error('Failed to downgrade plan.');
    },
  });
}

export function useBulkExecute() {
  return useMutation({
    mutationFn: async ({
      ids,
      action,
    }: {
      ids: string[];
      action: BulkAction;
    }) => {
      const res = await api.post<ApiResponse<{ jobId: string }>>(
        '/company/subscriptions/bulk',
        { ids, action }
      );
      return res.data.data;
    },
    onError: () => {
      toast.error('Bulk operation failed to start.');
    },
  });
}
