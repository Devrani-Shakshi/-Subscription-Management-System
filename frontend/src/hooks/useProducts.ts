import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '@/lib/axios';
import type { Product, ProductFormData } from '@/types/company';
import type { AxiosError } from 'axios';

interface ApiError {
  message: string;
}

interface ProductsResponse {
  data: Product[];
  meta?: { total: number; page: number; limit: number };
}

export function useProducts(page = 1, limit = 25) {
  return useQuery<ProductsResponse>({
    queryKey: ['products', page, limit],
    queryFn: async () => {
      const offset = (page - 1) * limit;
      const { data } = await api.get('/company/products', {
        params: { offset, limit },
      });
      return data;
    },
  });
}

export function useCreateProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: ProductFormData) => {
      const { data } = await api.post('/company/products', body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['products'] });
      toast.success('Product created');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to create product');
    },
  });
}

export function useUpdateProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: ProductFormData }) => {
      const { data } = await api.put(`/company/products/${id}`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['products'] });
      toast.success('Product updated');
    },
    onError: (err: AxiosError<ApiError>) => {
      toast.error(err.response?.data?.message || 'Failed to update product');
    },
  });
}

export function useDeleteProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/company/products/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['products'] });
      toast.success('Product deleted');
    },
    onError: (err: AxiosError<ApiError>) => {
      const msg = err.response?.status === 409
        ? 'Product used in active subscriptions.'
        : err.response?.data?.message || 'Failed to delete product';
      toast.error(msg);
    },
  });
}
