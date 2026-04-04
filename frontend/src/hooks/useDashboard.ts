import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/axios';
import type { DashboardData } from '@/types/company';

export function useCompanyDashboard() {
  return useQuery<DashboardData>({
    queryKey: ['company', 'dashboard'],
    queryFn: async () => {
      const { data } = await api.get('/company/dashboard');
      return data.data ?? data;
    },
    refetchInterval: 5 * 60 * 1000, // 5 minutes
    staleTime: 2 * 60 * 1000,
  });
}
