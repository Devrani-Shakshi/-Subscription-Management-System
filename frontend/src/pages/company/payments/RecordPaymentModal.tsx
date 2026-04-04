import React, { useState, useMemo } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Search } from 'lucide-react';
import { Modal, Button, FormField, Input, Select, DatePicker, Textarea } from '@/components/ui';
import { useRecordPayment, useUnpaidInvoices } from '@/hooks/usePayments';
import { formatCurrency, debounce } from '@/lib/utils';
import type { PaymentMethod, UnpaidInvoiceOption } from '@/types/billing';

interface RecordPaymentModalProps {
  open: boolean;
  onClose: () => void;
}

const METHOD_OPTIONS = [
  { label: 'Credit card', value: 'credit_card' },
  { label: 'Bank transfer', value: 'bank_transfer' },
  { label: 'Cash', value: 'cash' },
  { label: 'Check', value: 'check' },
  { label: 'Other', value: 'other' },
];

const schema = z.object({
  invoiceId: z.string().min(1, 'Select an invoice'),
  amount: z.number({ invalid_type_error: 'Enter a valid amount' }).positive('Amount must be greater than 0'),
  method: z.enum(['credit_card', 'bank_transfer', 'cash', 'check', 'other'] as const),
  date: z.string().min(1, 'Payment date is required'),
  notes: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export const RecordPaymentModal: React.FC<RecordPaymentModalProps> = ({ open, onClose }) => {
  const [search, setSearch] = useState('');
  const [selectedInv, setSelectedInv] = useState<UnpaidInvoiceOption | null>(null);

  const { data: unpaidRes } = useUnpaidInvoices(search);
  const unpaidInvoices = unpaidRes?.data ?? [];
  // Sort overdue first
  const sortedUnpaid = useMemo(
    () => [...unpaidInvoices].sort((a, b) => (b.isOverdue ? 1 : 0) - (a.isOverdue ? 1 : 0)),
    [unpaidInvoices]
  );

  const record = useRecordPayment();

  const {
    register,
    control,
    handleSubmit,
    setValue,
    setError,
    watch,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      invoiceId: '',
      amount: 0,
      method: 'credit_card',
      date: new Date().toISOString().split('T')[0],
      notes: '',
    },
  });

  const debouncedSearch = useMemo(
    () => debounce((v: string) => setSearch(v), 300),
    []
  );

  const onSubmit = (values: FormValues) => {
    // Validate amount doesn't exceed outstanding
    if (selectedInv && values.amount > selectedInv.amountDue) {
      setError('amount', {
        message: `Exceeds outstanding balance of ${formatCurrency(selectedInv.amountDue)}`,
      });
      return;
    }

    record.mutate(
      { ...values, notes: values.notes ?? '', method: values.method as PaymentMethod },
      {
        onSuccess: () => {
          reset();
          setSelectedInv(null);
          onClose();
        },
      }
    );
  };

  const handleClose = () => {
    reset();
    setSelectedInv(null);
    onClose();
  };

  return (
    <Modal open={open} onClose={handleClose} title="Record payment" size="md">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Invoice search */}
        <FormField label="Invoice" name="invoiceId" required error={errors.invoiceId?.message}>
          <Controller
            control={control}
            name="invoiceId"
            render={() => (
              <div className="space-y-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                  <Input
                    placeholder="Search unpaid invoices…"
                    className="pl-10"
                    value={selectedInv ? `${selectedInv.number} — ${selectedInv.customerName}` : search}
                    onChange={(e) => {
                      setSelectedInv(null);
                      setValue('invoiceId', '');
                      setValue('amount', 0);
                      debouncedSearch(e.target.value);
                      setSearch(e.target.value);
                    }}
                    error={!!errors.invoiceId}
                  />
                </div>
                {!selectedInv && sortedUnpaid.length > 0 && search.length > 0 && (
                  <div className="bg-gray-800 border border-gray-700 rounded-lg max-h-40 overflow-y-auto">
                    {sortedUnpaid.map((inv) => (
                      <button
                        key={inv.id}
                        type="button"
                        className="w-full text-left px-3 py-2 text-sm hover:bg-gray-700 transition-colors flex justify-between items-center"
                        onClick={() => {
                          setSelectedInv(inv);
                          setValue('invoiceId', inv.id);
                          setValue('amount', inv.amountDue);
                          setSearch('');
                        }}
                      >
                        <span>
                          <span className="font-mono font-medium text-gray-200">{inv.number}</span>
                          <span className="text-gray-400 ml-2">{inv.customerName}</span>
                        </span>
                        <span className={`font-medium ${inv.isOverdue ? 'text-red-400' : 'text-gray-300'}`}>
                          {formatCurrency(inv.amountDue)}
                          {inv.isOverdue && <span className="text-xs ml-1">(overdue)</span>}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          />
        </FormField>

        {/* Amount + Method */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormField label="Amount" name="amount" required error={errors.amount?.message}>
            <Input
              type="number"
              step="0.01"
              min="0"
              {...register('amount', { valueAsNumber: true })}
              error={!!errors.amount}
            />
          </FormField>
          <FormField label="Method" name="method" required error={errors.method?.message}>
            <Select options={METHOD_OPTIONS} {...register('method')} error={!!errors.method} />
          </FormField>
        </div>

        {/* Date */}
        <FormField label="Payment date" name="date" required error={errors.date?.message}>
          <DatePicker {...register('date')} error={!!errors.date} />
        </FormField>

        {/* Notes */}
        <FormField label="Notes" name="notes" hint="Optional">
          <Textarea {...register('notes')} placeholder="Additional notes…" rows={2} />
        </FormField>

        {/* Footer */}
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={handleClose}>Cancel</Button>
          <Button type="submit" loading={record.isPending}>Record payment</Button>
        </div>
      </form>
    </Modal>
  );
};
