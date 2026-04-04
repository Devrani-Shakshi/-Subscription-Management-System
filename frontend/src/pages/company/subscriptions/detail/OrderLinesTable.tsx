import React from 'react';
import { formatCurrency } from '@/lib/utils';
import type { OrderLine } from '@/types/subscription';

interface OrderLinesTableProps {
  orderLines: OrderLine[];
}

export const OrderLinesTable: React.FC<OrderLinesTableProps> = ({
  orderLines,
}) => {
  const subtotal = orderLines.reduce((sum, l) => sum + l.amount, 0);
  const totalTax = orderLines.reduce((sum, l) => sum + l.tax, 0);
  const grandTotal = subtotal + totalTax;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-800">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          Order Lines
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-xs font-semibold text-gray-500 uppercase">
              <th className="px-5 py-2.5 text-left">Product</th>
              <th className="px-3 py-2.5 text-center w-16">Qty</th>
              <th className="px-3 py-2.5 text-right w-24">Unit Price</th>
              <th className="px-3 py-2.5 text-right w-20">Tax</th>
              <th className="px-5 py-2.5 text-right w-24">Amount</th>
            </tr>
          </thead>
          <tbody>
            {orderLines.map((line) => (
              <tr key={line.id} className="border-b border-gray-800/30 last:border-0">
                <td className="px-5 py-3 text-gray-200">{line.productName}</td>
                <td className="px-3 py-3 text-center text-gray-400">{line.quantity}</td>
                <td className="px-3 py-3 text-right text-gray-400">
                  {formatCurrency(line.unitPrice)}
                </td>
                <td className="px-3 py-3 text-right text-gray-500">
                  {formatCurrency(line.tax)}
                </td>
                <td className="px-5 py-3 text-right text-gray-200 font-medium">
                  {formatCurrency(line.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Totals */}
      <div className="border-t border-gray-800 px-5 py-3 space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Subtotal</span>
          <span className="text-gray-300">{formatCurrency(subtotal)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Tax</span>
          <span className="text-gray-300">{formatCurrency(totalTax)}</span>
        </div>
        <div className="flex justify-between text-sm font-semibold pt-1 border-t border-gray-800">
          <span className="text-gray-200">Total</span>
          <span className="text-emerald-400">{formatCurrency(grandTotal)}</span>
        </div>
      </div>
    </div>
  );
};
