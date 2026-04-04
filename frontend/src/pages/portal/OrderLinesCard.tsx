import React from 'react';
import { formatCurrency } from '@/lib/utils';
import type { PortalSubscription } from '@/types/portal';

interface OrderLinesCardProps {
  subscription: PortalSubscription;
}

export const OrderLinesCard: React.FC<OrderLinesCardProps> = ({ subscription }) => {
  const { orderLines, subtotal, tax, discount, grandTotal } = subscription;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-800">
        <h3 className="text-sm font-semibold text-gray-200">Order Lines</h3>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="px-5 py-3 text-left text-xs font-semibold text-gray-400 uppercase">
                Product
              </th>
              <th className="px-5 py-3 text-right text-xs font-semibold text-gray-400 uppercase">
                Qty
              </th>
              <th className="px-5 py-3 text-right text-xs font-semibold text-gray-400 uppercase">
                Unit Price
              </th>
              <th className="px-5 py-3 text-right text-xs font-semibold text-gray-400 uppercase">
                Total
              </th>
            </tr>
          </thead>
          <tbody>
            {orderLines.map((line) => (
              <tr key={line.id} className="border-b border-gray-800/30 last:border-0">
                <td className="px-5 py-3 text-gray-200">{line.product}</td>
                <td className="px-5 py-3 text-right text-gray-300">{line.quantity}</td>
                <td className="px-5 py-3 text-right text-gray-300">
                  {formatCurrency(line.unitPrice)}
                </td>
                <td className="px-5 py-3 text-right text-gray-200 font-medium">
                  {formatCurrency(line.total)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Breakdown */}
      <div className="px-5 py-4 border-t border-gray-800 space-y-1.5">
        <div className="flex justify-between text-sm text-gray-400">
          <span>Subtotal</span>
          <span className="text-gray-300">{formatCurrency(subtotal)}</span>
        </div>
        {tax > 0 && (
          <div className="flex justify-between text-sm text-gray-400">
            <span>Tax</span>
            <span className="text-gray-300">{formatCurrency(tax)}</span>
          </div>
        )}
        {discount > 0 && (
          <div className="flex justify-between text-sm text-gray-400">
            <span>Discount</span>
            <span className="text-emerald-400">-{formatCurrency(discount)}</span>
          </div>
        )}
        <div className="flex justify-between text-base font-bold text-gray-100 pt-2 border-t border-gray-800">
          <span>Grand Total</span>
          <span>{formatCurrency(grandTotal)}</span>
        </div>
      </div>
    </div>
  );
};
