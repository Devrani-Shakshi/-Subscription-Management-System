import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/axios';
import toast from 'react-hot-toast';
import type { ApiResponse } from '@/types';
import type {
  AdminDashboardData,
  AdminCompanySummary,
  AdminCompanyDetail,
  AdminCompanyFilters,
  AdminSubscription,
  AdminCustomer,
  AdminInvoice,
  AuditEntry,
  AuditFilters,
  CreateCompanyPayload,
  SlugCheckResponse,
} from '@/types/admin';

// ─── Dashboard ────────────────────────────────────────────────────
export function useAdminDashboard() {
  return useQuery({
    queryKey: ['admin', 'dashboard'],
    queryFn: async () => {
      const res = await api.get<ApiResponse<AdminDashboardData>>(
        '/admin/dashboard'
      );
      return res.data.data;
    },
    staleTime: 5 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
  });
}

// ─── Companies List ───────────────────────────────────────────────
export function useCompanies(filters: AdminCompanyFilters) {
  return useQuery({
    queryKey: ['admin', 'companies', filters],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        page: filters.page,
        limit: filters.limit,
      };
      if (filters.status) params.status = filters.status;
      if (filters.search) params.search = filters.search;

      const res = await api.get<
        ApiResponse<AdminCompanySummary[]>
      >('/admin/companies', { params });
      return res.data;
    },
    staleTime: 30_000,
  });
}

// ─── Company Detail ───────────────────────────────────────────────
export function useCompanyDetail(tenantId: string) {
  return useQuery({
    queryKey: ['admin', 'companies', tenantId],
    queryFn: async () => {
      const res = await api.get<ApiResponse<AdminCompanyDetail>>(
        `/admin/companies/${tenantId}`
      );
      return res.data.data;
    },
    enabled: !!tenantId,
  });
}

// ─── Company Subscriptions ────────────────────────────────────────
export function useAdminCompanySubscriptions(
  tenantId: string,
  page = 1,
  limit = 10
) {
  return useQuery({
    queryKey: ['admin', 'companies', tenantId, 'subscriptions', page, limit],
    queryFn: async () => {
      const res = await api.get<ApiResponse<AdminSubscription[]>>(
        `/admin/companies/${tenantId}/subscriptions`,
        { params: { page, limit } }
      );
      return res.data;
    },
    enabled: !!tenantId,
  });
}

// ─── Company Customers ────────────────────────────────────────────
export function useAdminCompanyCustomers(
  tenantId: string,
  page = 1,
  limit = 10
) {
  return useQuery({
    queryKey: ['admin', 'companies', tenantId, 'customers', page, limit],
    queryFn: async () => {
      const res = await api.get<ApiResponse<AdminCustomer[]>>(
        `/admin/companies/${tenantId}/customers`,
        { params: { page, limit } }
      );
      return res.data;
    },
    enabled: !!tenantId,
  });
}

// ─── Company Invoices ─────────────────────────────────────────────
export function useAdminCompanyInvoices(
  tenantId: string,
  page = 1,
  limit = 10
) {
  return useQuery({
    queryKey: ['admin', 'companies', tenantId, 'invoices', page, limit],
    queryFn: async () => {
      const res = await api.get<ApiResponse<AdminInvoice[]>>(
        `/admin/companies/${tenantId}/invoices`,
        { params: { page, limit } }
      );
      return res.data;
    },
    enabled: !!tenantId,
  });
}

// ─── Audit Log ────────────────────────────────────────────────────
export function useAdminAudit(filters: AuditFilters) {
  return useQuery({
    queryKey: ['admin', 'audit', filters],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        page: filters.page,
        limit: filters.limit,
      };
      if (filters.companyId) params.companyId = filters.companyId;
      if (filters.entityType) params.entityType = filters.entityType;
      if (filters.action) params.action = filters.action;
      if (filters.actor) params.actor = filters.actor;
      if (filters.dateFrom) params.dateFrom = filters.dateFrom;
      if (filters.dateTo) params.dateTo = filters.dateTo;

      const res = await api.get<ApiResponse<AuditEntry[]>>(
        '/admin/audit',
        { params }
      );
      return res.data;
    },
  });
}

// ─── Mutations ────────────────────────────────────────────────────
export function useCreateCompany() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateCompanyPayload) => {
      const res = await api.post<ApiResponse<AdminCompanySummary>>(
        '/admin/companies',
        data
      );
      return res.data.data;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['admin', 'companies'] });
      toast.success(`Company created. Invite sent to ${variables.ownerEmail}.`);
    },
    onError: () => {
      toast.error('Failed to create company.');
    },
  });
}

export function useSuspendCompany() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`/admin/companies/${id}/suspend`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'companies'] });
      toast.success('Company suspended.');
    },
  });
}

export function useReactivateCompany() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`/admin/companies/${id}/reactivate`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'companies'] });
      toast.success('Company reactivated.');
    },
  });
}

export function useDeleteCompany() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/admin/companies/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'companies'] });
      toast.success('Company deleted.');
    },
  });
}

export function useCheckSlug(slug: string) {
  return useQuery({
    queryKey: ['admin', 'check-slug', slug],
    queryFn: async () => {
      const res = await api.get<ApiResponse<SlugCheckResponse>>(
        '/admin/companies/check-slug',
        { params: { slug } }
      );
      return res.data.data;
    },
    enabled: slug.length >= 2,
    staleTime: 10_000,
  });
}
