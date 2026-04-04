import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '@/lib/axios';
import type { Tax, TaxFormData } from '@/types/company';
import type { AxiosError } from 'axios';

interface ApiError {
  message: string;
}

interface TaxesResponse {
  data: Tax[];
  meta?: { total: number; page: number; limit: number };
}

export function useTaxes() {
  return useQuery<TaxesResponse>({
    queryKey: ['taxes'],
    queryFn: async () => {
      const { data } = await api.get('/company/taxes');
      return data;
    },
  });
}

export function useCreateTax() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: TaxFormData) => {
      const { data } = await api.post('/company/taxes', body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['taxes'] });
      toast.success('Tax created');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to create tax');
    },
  });
}

export function useUpdateTax() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: TaxFormData }) => {
      const { data } = await api.put(`/company/taxes/${id}`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['taxes'] });
      toast.success('Tax updated');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to update tax');
    },
  });
}

export function useDeleteTax() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/company/taxes/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['taxes'] });
      toast.success('Tax deleted');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to delete tax');
    },
  });
}
