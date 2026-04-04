import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '@/lib/axios';
import type { Template, TemplateFormData } from '@/types/company';
import type { AxiosError } from 'axios';

interface ApiError {
  message: string;
}

interface TemplatesResponse {
  data: Template[];
  meta?: { total: number; page: number; limit: number };
}

export function useTemplates(page = 1, limit = 25) {
  return useQuery<TemplatesResponse>({
    queryKey: ['templates', page, limit],
    queryFn: async () => {
      const offset = (page - 1) * limit;
      const { data } = await api.get('/company/templates', {
        params: { offset, limit },
      });
      return data;
    },
  });
}

export function useCreateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: TemplateFormData) => {
      const { data } = await api.post('/company/templates', body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['templates'] });
      toast.success('Template created');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to create template');
    },
  });
}

export function useUpdateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: TemplateFormData }) => {
      const { data } = await api.put(`/company/templates/${id}`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['templates'] });
      toast.success('Template updated');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to update template');
    },
  });
}

export function useDeleteTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/company/templates/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['templates'] });
      toast.success('Template deleted');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to delete template');
    },
  });
}
