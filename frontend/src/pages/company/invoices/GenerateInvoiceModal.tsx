import React, { useState, useMemo } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Search, Loader2 } from 'lucide-react';
import { Modal, Button, FormField, Input, DatePicker } from '@/components/ui';
import { useGenerateInvoice, useSubscriptionOptions, useSubscriptionPreview } from '@/hooks/useInvoices';
import { formatCurrency, debounce } from '@/lib/utils';
import type { SubscriptionOption } from '@/types/billing';

interface GenerateInvoiceModalProps {
  open: boolean;
  onClose: () => void;
}

const schema = z.object({
  subscriptionId: z.string().min(1, 'Select a subscription'),
  invoiceDate: z.string().min(1, 'Invoice date is required'),
  dueDate: z.string().min(1, 'Due date is required'),
});

type FormValues = z.infer<typeof schema>;

export const GenerateInvoiceModal: React.FC<GenerateInvoiceModalProps> = ({
  open,
  onClose,
}) => {
  const [search, setSearch] = useState('');
  const [selectedSub, setSelectedSub] = useState<SubscriptionOption | null>(null);

  const { data: optionsRes } = useSubscriptionOptions(search);
  const options = optionsRes?.data ?? [];

  const generate = useGenerateInvoice();

  const {
    register,
    control,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { subscriptionId: '', invoiceDate: '', dueDate: '' },
  });

  const subscriptionId = watch('subscriptionId');
  const { data: previewRes, isLoading: previewLoading } = useSubscriptionPreview(subscriptionId);
  const lineItems = previewRes?.data ?? [];

  const previewTotal = useMemo(
    () => lineItems.reduce((sum, li) => sum + li.amount, 0),
    [lineItems]
  );

  const debouncedSearch = useMemo(
    () => debounce((v: string) => setSearch(v), 300),
    []
  );

  const onSubmit = (values: FormValues) => {
    generate.mutate(values, {
      onSuccess: () => {
        reset();
        setSelectedSub(null);
        onClose();
      },
    });
  };

  const handleClose = () => {
    reset();
    setSelectedSub(null);
    onClose();
  };

  return (
    <Modal open={open} onClose={handleClose} title="Generate invoice" size="lg">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Subscription search */}
        <FormField label="Subscription" name="subscriptionId" required error={errors.subscriptionId?.message}>
          <Controller
            control={control}
            name="subscriptionId"
            render={() => (
              <div className="space-y-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                  <Input
                    placeholder="Search subscriptions…"
                    className="pl-10"
                    value={selectedSub ? `${selectedSub.name} — ${selectedSub.customerName}` : search}
                    onChange={(e) => {
                      setSelectedSub(null);
                      setValue('subscriptionId', '');
                      debouncedSearch(e.target.value);
                      setSearch(e.target.value);
                    }}
                    error={!!errors.subscriptionId}
                  />
                </div>
                {!selectedSub && options.length > 0 && search.length > 0 && (
                  <div className="bg-gray-800 border border-gray-700 rounded-lg max-h-40 overflow-y-auto">
                    {options.map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        className="w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-gray-700 transition-colors"
                        onClick={() => {
                          setSelectedSub(opt);
                          setValue('subscriptionId', opt.id);
                          setSearch('');
                        }}
                      >
                        <span className="font-medium">{opt.name}</span>
                        <span className="text-gray-400 ml-2">— {opt.customerName}</span>
                        <span className="text-gray-500 ml-2">{formatCurrency(opt.amount)}/mo</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          />
        </FormField>

        {/* Dates */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormField label="Invoice date" name="invoiceDate" required error={errors.invoiceDate?.message}>
            <DatePicker {...register('invoiceDate')} error={!!errors.invoiceDate} />
          </FormField>
          <FormField label="Due date" name="dueDate" required error={errors.dueDate?.message}>
            <DatePicker {...register('dueDate')} error={!!errors.dueDate} />
          </FormField>
        </div>

        {/* Preview */}
        {subscriptionId && (
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-sm font-semibold text-gray-300 mb-3">Line items preview</h4>
            {previewLoading ? (
              <div className="flex items-center gap-2 text-gray-500 text-sm">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading…
              </div>
            ) : lineItems.length > 0 ? (
              <>
                <div className="space-y-2">
                  {lineItems.map((li) => (
                    <div key={li.id} className="flex justify-between text-sm">
                      <span className="text-gray-300">{li.product} × {li.quantity}</span>
                      <span className="text-gray-200 font-medium">{formatCurrency(li.amount)}</span>
                    </div>
                  ))}
                </div>
                <div className="border-t border-gray-700 mt-3 pt-3 flex justify-between">
                  <span className="text-sm font-semibold text-gray-200">Total</span>
                  <span className="text-sm font-bold text-violet-400">{formatCurrency(previewTotal)}</span>
                </div>
              </>
            ) : (
              <p className="text-sm text-gray-500">No line items</p>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={handleClose}>Cancel</Button>
          <Button type="submit" loading={generate.isPending}>Generate invoice</Button>
        </div>
      </form>
    </Modal>
  );
};
