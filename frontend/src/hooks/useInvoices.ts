import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '@/lib/axios';
import type { ApiResponse } from '@/types';
import type {
  Invoice,
  InvoiceFilters,
  GenerateInvoicePayload,
  InvoiceLineItem,
  SubscriptionOption,
} from '@/types/billing';

/* ── List ─────────────────────────────────────────── */

export function useInvoices(filters: InvoiceFilters) {
  return useQuery({
    queryKey: ['invoices', filters],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<Invoice[]>>(
        '/company/invoices',
        { params: filters }
      );
      return data;
    },
  });
}

/* ── Detail ───────────────────────────────────────── */

export function useInvoice(id: string) {
  return useQuery({
    queryKey: ['invoice', id],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<Invoice>>(
        `/company/invoices/${id}`
      );
      return data;
    },
    enabled: !!id,
  });
}

/* ── Generate ─────────────────────────────────────── */

export function useGenerateInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: GenerateInvoicePayload) => {
      const { data } = await api.post<ApiResponse<Invoice>>(
        '/company/invoices/generate',
        payload
      );
      return data;
    },
    onSuccess: () => {
      toast.success('Invoice generated');
      qc.invalidateQueries({ queryKey: ['invoices'] });
    },
  });
}

/* ── Confirm ──────────────────────────────────────── */

export function useConfirmInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post<ApiResponse<Invoice>>(
        `/company/invoices/${id}/confirm`
      );
      return data;
    },
    onSuccess: () => {
      toast.success('Invoice confirmed');
      qc.invalidateQueries({ queryKey: ['invoices'] });
      qc.invalidateQueries({ queryKey: ['invoice'] });
    },
  });
}

/* ── Send email ───────────────────────────────────── */

export function useSendInvoice() {
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post<ApiResponse<{ email: string }>>(
        `/company/invoices/${id}/send`
      );
      return data;
    },
    onSuccess: (res) => {
      toast.success(`Invoice sent to ${res.data.email}`);
    },
  });
}

/* ── Cancel ───────────────────────────────────────── */

export function useCancelInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post<ApiResponse<Invoice>>(
        `/company/invoices/${id}/cancel`
      );
      return data;
    },
    onSuccess: () => {
      toast.success('Invoice cancelled');
      qc.invalidateQueries({ queryKey: ['invoices'] });
      qc.invalidateQueries({ queryKey: ['invoice'] });
    },
  });
}

/* ── Download PDF ─────────────────────────────────── */

export function useDownloadInvoicePdf() {
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.get(`/company/invoices/${id}/pdf`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data as BlobPart]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice-${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    },
    onSuccess: () => {
      toast.success('PDF downloaded');
    },
  });
}

/* ── Preview line items (for generate modal) ──────── */

export function useSubscriptionPreview(subscriptionId: string) {
  return useQuery({
    queryKey: ['subscription-preview', subscriptionId],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<InvoiceLineItem[]>>(
        `/company/subscriptions/${subscriptionId}/preview`
      );
      return data;
    },
    enabled: !!subscriptionId,
  });
}

/* ── Available subscriptions ──────────────────────── */

export function useSubscriptionOptions(search: string) {
  return useQuery({
    queryKey: ['subscription-options', search],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<SubscriptionOption[]>>(
        '/company/subscriptions/options',
        { params: { search } }
      );
      return data;
    },
  });
}
