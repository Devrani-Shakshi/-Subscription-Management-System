import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '@/lib/axios';
import type { ApiResponse } from '@/types';
import type {
  Payment,
  PaymentFilters,
  PaymentSummary,
  RecordPaymentPayload,
  UnpaidInvoiceOption,
} from '@/types/billing';

/* ── List ─────────────────────────────────────────── */

export function usePayments(filters: PaymentFilters) {
  return useQuery({
    queryKey: ['payments', filters],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<Payment[]>>(
        '/company/payments',
        { params: filters }
      );
      return data;
    },
  });
}

/* ── Summary ──────────────────────────────────────── */

export function usePaymentSummary() {
  return useQuery({
    queryKey: ['payment-summary'],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<PaymentSummary>>(
        '/company/payments/summary'
      );
      return data;
    },
  });
}

/* ── Record payment ───────────────────────────────── */

export function useRecordPayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: RecordPaymentPayload) => {
      const { data } = await api.post<ApiResponse<Payment>>(
        '/company/payments',
        payload
      );
      return data;
    },
    onSuccess: () => {
      toast.success('Payment recorded');
      qc.invalidateQueries({ queryKey: ['payments'] });
      qc.invalidateQueries({ queryKey: ['payment-summary'] });
      qc.invalidateQueries({ queryKey: ['invoices'] });
    },
  });
}

/* ── Unpaid invoices (for select) ─────────────────── */

export function useUnpaidInvoices(search: string) {
  return useQuery({
    queryKey: ['unpaid-invoices', search],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<UnpaidInvoiceOption[]>>(
        '/company/invoices/unpaid',
        { params: { search } }
      );
      return data;
    },
  });
}
