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
      const res = await api.get('/admin/dashboard');
      const raw = res.data;

      // Transform backend shape → frontend AdminDashboardData
      const metrics = raw.metrics || [];
      const findMetric = (label: string) => {
        const m = metrics.find((x: { label: string }) => x.label === label);
        if (!m) return 0;
        const v = m.value?.replace?.(/[$,%]/g, '').replace(/,/g, '') ?? m.value;
        return Number(v) || 0;
      };

      const breakdown = raw.company_breakdown || [];
      const topCompanies = breakdown.map((c: Record<string, unknown>) => ({
        id: c.tenant_id,
        name: c.name,
        slug: '',
        status: c.status,
        mrr: Number(c.mrr) || 0,
        activeSubs: c.active_subs ?? 0,
        trialEnds: null,
        createdAt: '',
        ownerEmail: '',
        hasActiveSubscriptions: (c.active_subs as number) > 0,
      }));

      const alerts = (raw.alerts || []).map((a: Record<string, unknown>, i: number) => ({
        id: a.tenant_id || String(i),
        type: a.severity === 'error' ? 'suspended' : 'trial_expiring',
        severity: a.severity === 'error' ? 'high' : 'medium',
        companyName: a.tenant_name || '',
        companyId: a.tenant_id || '',
        message: a.message || '',
        createdAt: new Date().toISOString(),
      }));

      return {
        totalCompanies: findMetric('Total Companies'),
        totalActiveSubs: findMetric('Active Subscriptions'),
        platformMRR: findMetric('Platform MRR'),
        platformChurnRate: 0,
        newCompaniesThisMonth: findMetric('New Companies (This Month)'),
        alerts,
        topCompanies,
      };
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
        page_size: filters.limit,
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
      const res = await api.get(`/admin/companies/${tenantId}`);
      const c = res.data;
      return {
        id: c.id,
        name: c.name,
        slug: c.slug,
        status: c.status,
        mrr: Number(c.mrr) || 0,
        activeSubs: c.active_subs_count ?? 0,
        trialEnds: c.trial_ends_at || null,
        createdAt: c.created_at || '',
        ownerEmail: c.owner_email || '',
        hasActiveSubscriptions: (c.active_subs_count ?? 0) > 0,
        totalCustomers: c.total_customers ?? 0,
        totalInvoices: c.total_invoices ?? 0,
      };
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
      // Map frontend camelCase → backend snake_case field names
      const res = await api.post('/admin/companies', {
        name: data.companyName,
        slug: data.slug,
        email: data.ownerEmail,
      });
      return res.data;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['admin', 'companies'] });
      qc.invalidateQueries({ queryKey: ['admin', 'dashboard'] });
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
      const res = await api.get(
        '/admin/companies/check-slug',
        { params: { slug } }
      );
      return res.data;
    },
    enabled: slug.length >= 2,
    staleTime: 10_000,
  });
}
