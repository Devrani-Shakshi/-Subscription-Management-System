import React from 'react';
import { User, CreditCard, Package, Calendar, FileText } from 'lucide-react';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { WizardFormData } from '@/types/subscription';

interface StepReviewProps {
  formData: WizardFormData;
}

const TERMS_LABEL: Record<string, string> = {
  net_7: 'Net 7',
  net_15: 'Net 15',
  net_30: 'Net 30',
  due_on_receipt: 'Due on receipt',
};

export const StepReview: React.FC<StepReviewProps> = ({ formData }) => {
  const total = formData.products.reduce(
    (sum, p) => sum + p.quantity * p.unitPrice,
    0
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">Review & Confirm</h2>
        <p className="mt-1 text-sm text-gray-400">
          Double-check everything before creating the subscription.
        </p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl divide-y divide-gray-800">
        {/* Customer */}
        <div className="flex items-center gap-3 px-5 py-4">
          <div className="h-9 w-9 rounded-lg bg-violet-600/10 flex items-center justify-center">
            <User className="h-4 w-4 text-violet-400" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Customer</p>
            <p className="text-sm font-medium text-gray-100">{formData.customerName}</p>
          </div>
        </div>

        {/* Plan */}
        <div className="flex items-center gap-3 px-5 py-4">
          <div className="h-9 w-9 rounded-lg bg-teal-600/10 flex items-center justify-center">
            <CreditCard className="h-4 w-4 text-teal-400" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Plan</p>
            <p className="text-sm font-medium text-gray-100">{formData.planName}</p>
          </div>
        </div>

        {/* Dates */}
        <div className="flex items-center gap-3 px-5 py-4">
          <div className="h-9 w-9 rounded-lg bg-amber-600/10 flex items-center justify-center">
            <Calendar className="h-4 w-4 text-amber-400" />
          </div>
          <div className="flex gap-6">
            <div>
              <p className="text-xs text-gray-500">Start</p>
              <p className="text-sm text-gray-200">
                {formData.startDate ? formatDate(formData.startDate) : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Expiry</p>
              <p className="text-sm text-gray-200">
                {formData.expiryDate ? formatDate(formData.expiryDate) : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Terms</p>
              <p className="text-sm text-gray-200">
                {TERMS_LABEL[formData.paymentTerms]}
              </p>
            </div>
          </div>
        </div>

        {/* Products */}
        {formData.products.length > 0 && (
          <div className="px-5 py-4 space-y-3">
            <div className="flex items-center gap-2">
              <Package className="h-4 w-4 text-gray-500" />
              <p className="text-xs text-gray-500 uppercase font-semibold">Products</p>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500">
                  <th className="text-left pb-1">Product</th>
                  <th className="text-center pb-1 w-16">Qty</th>
                  <th className="text-right pb-1 w-24">Price</th>
                  <th className="text-right pb-1 w-24">Total</th>
                </tr>
              </thead>
              <tbody>
                {formData.products.map((p) => (
                  <tr key={p.productId} className="border-t border-gray-800/30">
                    <td className="py-2 text-gray-200">{p.productName}</td>
                    <td className="py-2 text-center text-gray-400">{p.quantity}</td>
                    <td className="py-2 text-right text-gray-400">
                      {formatCurrency(p.unitPrice)}
                    </td>
                    <td className="py-2 text-right text-gray-200">
                      {formatCurrency(p.quantity * p.unitPrice)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Notes */}
        {formData.notes && (
          <div className="flex items-start gap-3 px-5 py-4">
            <div className="h-9 w-9 rounded-lg bg-gray-800 flex items-center justify-center mt-0.5">
              <FileText className="h-4 w-4 text-gray-500" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Notes</p>
              <p className="text-sm text-gray-300 whitespace-pre-wrap">{formData.notes}</p>
            </div>
          </div>
        )}
      </div>

      {/* Total MRR */}
      <div className="flex items-center justify-between p-5 rounded-xl
                      bg-gradient-to-r from-violet-600/10 to-emerald-600/10
                      border border-violet-500/20">
        <span className="text-sm font-medium text-gray-300">Total MRR</span>
        <span className="text-2xl font-bold text-emerald-400">
          {formatCurrency(total)}
          <span className="text-sm font-normal text-gray-500">/mo</span>
        </span>
      </div>
    </div>
  );
};
