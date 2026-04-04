import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/axios';
import type { ChurnScoreEntry, ChurnFilters } from '@/types/company';
import type { ApiResponse, ApiMeta } from '@/types';

interface ChurnListResponse {
  data: ChurnScoreEntry[];
  meta: ApiMeta;
}

export function useChurnScores(filters: ChurnFilters) {
  return useQuery<ChurnListResponse>({
    queryKey: ['company', 'churn', filters],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        offset: (filters.page - 1) * filters.limit,
        limit: filters.limit,
      };
      if (filters.min_score !== undefined) params.min_score = filters.min_score;

      const { data } = await api.get('/company/churn');
      const items: ChurnScoreEntry[] = data.items ?? data.data ?? [];
      return {
        data: items,
        meta: {
          total: data.total ?? items.length,
          page: filters.page,
          limit: filters.limit,
        },
      };
    },
  });
}
