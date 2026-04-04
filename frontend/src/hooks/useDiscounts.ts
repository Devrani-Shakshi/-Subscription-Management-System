import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '@/lib/axios';
import type { Discount, DiscountFormData } from '@/types/company';
import type { AxiosError } from 'axios';

interface ApiError {
  message: string;
}

interface DiscountsResponse {
  data: Discount[];
  meta?: { total: number; page: number; limit: number };
}

export function useDiscounts(page = 1, limit = 25) {
  return useQuery<DiscountsResponse>({
    queryKey: ['discounts', page, limit],
    queryFn: async () => {
      const offset = (page - 1) * limit;
      const { data } = await api.get('/company/discounts', {
        params: { offset, limit },
      });
      return data;
    },
  });
}

export function useCreateDiscount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: DiscountFormData) => {
      const { data } = await api.post('/company/discounts', body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['discounts'] });
      toast.success('Discount created');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to create discount');
    },
  });
}

export function useUpdateDiscount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: DiscountFormData }) => {
      const { data } = await api.put(`/company/discounts/${id}`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['discounts'] });
      toast.success('Discount updated');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to update discount');
    },
  });
}

export function useDeleteDiscount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/company/discounts/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['discounts'] });
      toast.success('Discount deleted');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to delete discount');
    },
  });
}
