import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '@/lib/axios';
import type { Customer, CustomerDetail } from '@/types/company';
import type { AxiosError } from 'axios';

interface ApiError {
  message: string;
}

interface CustomersResponse {
  data: Customer[];
  meta?: { total: number; page: number; limit: number };
}

interface CustomerFilters {
  search?: string;
  status?: string;
  churn_risk?: string;
}

export function useCustomers(
  page = 1,
  limit = 25,
  filters?: CustomerFilters
) {
  return useQuery<CustomersResponse>({
    queryKey: ['customers', page, limit, filters],
    queryFn: async () => {
      const offset = (page - 1) * limit;
      const { data } = await api.get('/company/customers', {
        params: { offset, limit, ...filters },
      });
      return data;
    },
  });
}

export function useCustomerDetail(id: string) {
  return useQuery<CustomerDetail>({
    queryKey: ['customers', id],
    queryFn: async () => {
      const { data } = await api.get(`/company/customers/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useInviteCustomer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { email: string }) => {
      const { data } = await api.post('/company/customers/invite', body);
      return data;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['customers'] });
      toast.success(`Invite sent to ${variables.email}`);
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to send invite');
    },
  });
}
