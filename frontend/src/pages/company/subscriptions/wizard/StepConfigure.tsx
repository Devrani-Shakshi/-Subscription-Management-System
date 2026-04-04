import React from 'react';
import { FormField, DatePicker, Select, Textarea } from '@/components/ui';
import type { WizardFormData, PaymentTerms } from '@/types/subscription';

interface StepConfigureProps {
  formData: WizardFormData;
  setData: (data: Partial<WizardFormData>) => void;
}

const PAYMENT_TERMS_OPTIONS = [
  { label: 'Net 7', value: 'net_7' as PaymentTerms },
  { label: 'Net 15', value: 'net_15' as PaymentTerms },
  { label: 'Net 30', value: 'net_30' as PaymentTerms },
  { label: 'Due on receipt', value: 'due_on_receipt' as PaymentTerms },
];

export const StepConfigure: React.FC<StepConfigureProps> = ({
  formData,
  setData,
}) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">Configure</h2>
        <p className="mt-1 text-sm text-gray-400">
          Set billing dates, payment terms, and any additional notes.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <FormField label="Start Date" name="startDate" required>
          <DatePicker
            id="startDate"
            value={formData.startDate}
            onChange={(e) => setData({ startDate: e.target.value })}
          />
        </FormField>

        <FormField label="Expiry Date" name="expiryDate" required>
          <DatePicker
            id="expiryDate"
            value={formData.expiryDate}
            onChange={(e) => setData({ expiryDate: e.target.value })}
            min={formData.startDate || undefined}
          />
        </FormField>

        <FormField label="Payment Terms" name="paymentTerms" required>
          <Select
            id="paymentTerms"
            value={formData.paymentTerms}
            onChange={(e) =>
              setData({ paymentTerms: e.target.value as PaymentTerms })
            }
            options={PAYMENT_TERMS_OPTIONS}
          />
        </FormField>
      </div>

      <FormField label="Notes" name="notes" hint="Optional internal notes">
        <Textarea
          id="notes"
          value={formData.notes}
          onChange={(e) => setData({ notes: e.target.value })}
          placeholder="Add any notes for this subscription…"
          rows={4}
        />
      </FormField>
    </div>
  );
};
