import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/axios';
import type { AuditLogEntry, AuditFilters } from '@/types/company';
import type { ApiMeta } from '@/types';

interface AuditListResponse {
  data: AuditLogEntry[];
  meta: ApiMeta;
}

export function useCompanyAudit(filters: AuditFilters) {
  return useQuery<AuditListResponse>({
    queryKey: ['company', 'audit', filters],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        page: filters.page,
        page_size: filters.page_size,
      };
      if (filters.entity_type) params.entity_type = filters.entity_type;
      if (filters.action) params.action = filters.action;

      const { data } = await api.get('/company/audit', { params });
      const items: AuditLogEntry[] = data.items ?? data.data ?? [];
      return {
        data: items,
        meta: {
          total: data.total ?? items.length,
          page: data.page ?? filters.page,
          limit: data.page_size ?? filters.page_size,
        },
      };
    },
  });
}

export function useAuditExportUrl(filters: Omit<AuditFilters, 'page' | 'page_size'>) {
  const params = new URLSearchParams();
  if (filters.entity_type) params.set('entity_type', filters.entity_type);
  if (filters.action) params.set('action', filters.action);
  return `/company/audit/export?${params.toString()}`;
}
