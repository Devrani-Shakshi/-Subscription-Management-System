import { useQuery } from '@tanstack/react-query';
import api from '@/lib/axios';
import type { ApiResponse } from '@/types';
import type {
  DunningSchedule,
  DunningFilters,
  DunningSummary,
} from '@/types/billing';

/* ── List ─────────────────────────────────────────── */

export function useDunningSchedules(filters: DunningFilters) {
  return useQuery({
    queryKey: ['dunning', filters],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<DunningSchedule[]>>(
        '/company/dunning',
        { params: filters }
      );
      return data;
    },
  });
}

/* ── Summary ──────────────────────────────────────── */

export function useDunningSummary() {
  return useQuery({
    queryKey: ['dunning-summary'],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<DunningSummary>>(
        '/company/dunning/summary'
      );
      return data;
    },
  });
}
