import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '@/lib/axios';
import type { Plan, PlanFormData } from '@/types/company';
import type { AxiosError } from 'axios';

interface ApiError {
  message: string;
}

interface PlansResponse {
  data: Plan[];
  meta?: { total: number; page: number; limit: number };
}

export function usePlans(page = 1, limit = 25) {
  return useQuery<PlansResponse>({
    queryKey: ['plans', page, limit],
    queryFn: async () => {
      const offset = (page - 1) * limit;
      const { data } = await api.get('/company/plans', {
        params: { offset, limit },
      });
      return data;
    },
  });
}

export function useActivePlans() {
  return useQuery<PlansResponse>({
    queryKey: ['plans', 'active'],
    queryFn: async () => {
      const { data } = await api.get('/company/plans', {
        params: { status: 'active', limit: 100 },
      });
      return data;
    },
  });
}

export function useCreatePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: PlanFormData) => {
      const { data } = await api.post('/company/plans', body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['plans'] });
      toast.success('Plan created');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to create plan');
    },
  });
}

export function useUpdatePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: PlanFormData }) => {
      const { data } = await api.put(`/company/plans/${id}`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['plans'] });
      toast.success('Plan updated');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to update plan');
    },
  });
}

export function useDeletePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/company/plans/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['plans'] });
      toast.success('Plan deleted');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to delete plan');
    },
  });
}
