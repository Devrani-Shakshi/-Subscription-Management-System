import { useQuery } from '@tanstack/react-query';
import api from '@/lib/axios';
import type { ApiResponse } from '@/types';
import type { RevenueData, RevenueFilters } from '@/types/billing';

/* ── Timeline ─────────────────────────────────────── */

export function useRevenue(filters: RevenueFilters) {
  return useQuery({
    queryKey: ['revenue', filters],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<RevenueData>>(
        '/company/revenue/timeline',
        { params: filters }
      );
      return data;
    },
  });
}
