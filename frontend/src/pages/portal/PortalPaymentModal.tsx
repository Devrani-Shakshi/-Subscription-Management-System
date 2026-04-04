import React, { useState, useEffect, useCallback } from 'react';
import { CheckCircle, Loader2, AlertCircle, CreditCard, X } from 'lucide-react';
import { createPortal } from 'react-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button, FormField, Input } from '@/components/ui';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { usePortalPayment } from '@/hooks/usePortal';
import { paymentSchema } from '@/lib/portalValidations';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { PaymentFormData } from '@/lib/portalValidations';
import type { PortalInvoice, PaymentState } from '@/types/portal';

interface PortalPaymentModalProps {
  open: boolean;
  onClose: () => void;
  invoice: PortalInvoice | null;
}

export const PortalPaymentModal: React.FC<PortalPaymentModalProps> = ({
  open,
  onClose,
  invoice,
}) => {
  const { isMobile } = useBreakpoint();
  const [payState, setPayState] = useState<PaymentState>('idle');
  const payMutation = usePortalPayment();

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<PaymentFormData>({
    resolver: zodResolver(paymentSchema),
    defaultValues: { cardNumber: '', expiry: '', cvv: '', cardholderName: '' },
  });

  const cardNumber = watch('cardNumber');

  // Format card number as XXXX XXXX XXXX XXXX
  const handleCardChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, '').slice(0, 16);
    const formatted = raw.replace(/(\d{4})(?=\d)/g, '$1 ');
    setValue('cardNumber', formatted, { shouldValidate: true });
  };

  // Format expiry as MM/YY
  const handleExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let raw = e.target.value.replace(/\D/g, '').slice(0, 4);
    if (raw.length >= 3) {
      raw = raw.slice(0, 2) + '/' + raw.slice(2);
    }
    setValue('expiry', raw, { shouldValidate: true });
  };

  const handleClose = useCallback(() => {
    setPayState('idle');
    reset();
    onClose();
  }, [onClose, reset]);

  // Auto-close on success
  useEffect(() => {
    if (payState === 'success') {
      const timer = setTimeout(handleClose, 2000);
      return () => clearTimeout(timer);
    }
  }, [payState, handleClose]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    },
    [handleClose]
  );

  useEffect(() => {
    if (open) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [open, handleKeyDown]);

  const onSubmit = (data: PaymentFormData) => {
    if (!invoice) return;
    setPayState('processing');
    payMutation.mutate(
      {
        invoiceId: invoice.id,
        cardNumber: data.cardNumber.replace(/\s/g, ''),
        expiry: data.expiry,
        cvv: data.cvv,
        cardholderName: data.cardholderName,
      },
      {
        onSuccess: () => setPayState('success'),
        onError: () => setPayState('error'),
      }
    );
  };

  if (!open || !invoice) return null;

  const renderContent = () => {
    if (payState === 'success') {
      return (
        <div className="flex flex-col items-center justify-center py-10">
          <div className="h-16 w-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-4 animate-scale-in">
            <CheckCircle className="h-8 w-8 text-emerald-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-100 mb-1">Payment successful!</h3>
          <p className="text-sm text-gray-500">Redirecting...</p>
        </div>
      );
    }

    return (
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Invoice info */}
        <div className="rounded-lg bg-gray-800/50 p-4 space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Invoice</span>
            <span className="text-gray-200 font-mono">{invoice.number}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Amount due</span>
            <span className="text-gray-100 font-semibold">{formatCurrency(invoice.amount)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Due date</span>
            <span className="text-gray-300">{formatDate(invoice.dueDate)}</span>
          </div>
        </div>

        {/* Card number */}
        <FormField label="Card number" name="cardNumber" error={errors.cardNumber?.message}>
          <Input
            id="cardNumber"
            placeholder="4242 4242 4242 4242"
            value={cardNumber}
            onChange={handleCardChange}
            error={!!errors.cardNumber}
            maxLength={19}
            inputMode="numeric"
            autoComplete="cc-number"
          />
        </FormField>

        {/* Expiry + CVV */}
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Expiry" name="expiry" error={errors.expiry?.message}>
            <Input
              id="expiry"
              placeholder="MM/YY"
              {...register('expiry')}
              onChange={handleExpiryChange}
              error={!!errors.expiry}
              maxLength={5}
              inputMode="numeric"
              autoComplete="cc-exp"
            />
          </FormField>
          <FormField label="CVV" name="cvv" error={errors.cvv?.message}>
            <Input
              id="cvv"
              placeholder="123"
              {...register('cvv')}
              error={!!errors.cvv}
              maxLength={4}
              inputMode="numeric"
              type="password"
              autoComplete="cc-csc"
            />
          </FormField>
        </div>

        {/* Cardholder */}
        <FormField label="Cardholder name" name="cardholderName" error={errors.cardholderName?.message}>
          <Input
            id="cardholderName"
            placeholder="John Doe"
            {...register('cardholderName')}
            error={!!errors.cardholderName}
            autoComplete="cc-name"
          />
        </FormField>

        {/* Error state */}
        {payState === 'error' && (
          <div className="rounded-lg bg-red-500/5 border border-red-500/20 px-4 py-3 flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm text-red-300">Card declined. Please try a different card.</p>
              <button
                type="button"
                onClick={() => setPayState('idle')}
                className="text-xs text-red-400 hover:text-red-300 underline mt-1"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* Submit */}
        <Button
          type="submit"
          variant="amber"
          size="lg"
          className="w-full"
          loading={payState === 'processing'}
          disabled={payState === 'processing'}
        >
          <CreditCard className="h-4 w-4" />
          Pay {formatCurrency(invoice.amount)}
        </Button>
      </form>
    );
  };

  const modal = (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={handleClose}
        aria-hidden="true"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Payment"
        className={`
          relative w-full bg-gray-900 border border-gray-800
          overflow-hidden flex flex-col max-h-[90dvh]
          ${
            isMobile
              ? 'rounded-t-2xl animate-slide-up'
              : 'max-w-[480px] rounded-xl mx-4 animate-scale-in shadow-2xl shadow-black/50'
          }
        `.trim()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <h2 className="text-lg font-semibold text-gray-100">Make Payment</h2>
          <button
            onClick={handleClose}
            className="h-8 w-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {renderContent()}
        </div>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
};
