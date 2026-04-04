import React from 'react';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Invoice } from '@/types/billing';

interface InvoicePaperCardProps {
  invoice: Invoice;
}

export const InvoicePaperCard: React.FC<InvoicePaperCardProps> = ({ invoice }) => {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-800 bg-gradient-to-r from-violet-500/5 to-transparent">
        <div className="flex items-start justify-between">
          <div>
            <div className="h-8 w-8 rounded-lg bg-violet-500/20 flex items-center justify-center mb-3">
              <span className="text-violet-400 font-bold text-sm">S</span>
            </div>
            <p className="text-sm text-gray-400">From your company</p>
          </div>
          <div className="text-right">
            <h2 className="text-2xl font-bold text-gray-100 tracking-tight">INVOICE</h2>
            <p className="font-mono text-sm text-violet-400 mt-1">{invoice.number}</p>
            <div className="mt-2 space-y-0.5 text-xs text-gray-500">
              <p>Issued: {formatDate(invoice.invoiceDate)}</p>
              <p>Due: {formatDate(invoice.dueDate)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Bill to */}
      <div className="px-6 py-4 border-b border-gray-800/50">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Bill to</p>
        <p className="text-sm font-medium text-gray-200">{invoice.customerName}</p>
        <p className="text-sm text-gray-400">{invoice.customerEmail}</p>
        {invoice.customerAddress && (
          <p className="text-sm text-gray-500 mt-0.5">{invoice.customerAddress}</p>
        )}
      </div>

      {/* Line items */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Item</th>
              <th className="text-right px-3 py-3 text-xs font-semibold text-gray-500 uppercase">Qty</th>
              <th className="text-right px-3 py-3 text-xs font-semibold text-gray-500 uppercase">Price</th>
              <th className="text-right px-3 py-3 text-xs font-semibold text-gray-500 uppercase">Tax</th>
              <th className="text-right px-3 py-3 text-xs font-semibold text-gray-500 uppercase">Disc</th>
              <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Amount</th>
            </tr>
          </thead>
          <tbody>
            {invoice.lineItems.map((li) => (
              <tr key={li.id} className="border-b border-gray-800/30">
                <td className="px-6 py-3">
                  <p className="text-gray-200 font-medium">{li.product}</p>
                  {li.description && <p className="text-xs text-gray-500">{li.description}</p>}
                </td>
                <td className="text-right px-3 py-3 text-gray-300">{li.quantity}</td>
                <td className="text-right px-3 py-3 text-gray-300">{formatCurrency(li.unitPrice)}</td>
                <td className="text-right px-3 py-3 text-gray-400">{li.taxPercent}%</td>
                <td className="text-right px-3 py-3 text-gray-400">
                  {li.discount > 0 ? formatCurrency(li.discount) : '—'}
                </td>
                <td className="text-right px-6 py-3 text-gray-100 font-medium">
                  {formatCurrency(li.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Totals */}
      <div className="px-6 py-4 border-t border-gray-800 space-y-2">
        <div className="flex justify-between text-sm text-gray-400">
          <span>Subtotal</span>
          <span>{formatCurrency(invoice.subtotal)}</span>
        </div>
        {invoice.discountTotal > 0 && (
          <div className="flex justify-between text-sm text-emerald-400">
            <span>Discount</span>
            <span>−{formatCurrency(invoice.discountTotal)}</span>
          </div>
        )}
        <div className="flex justify-between text-sm text-gray-400">
          <span>Tax</span>
          <span>{formatCurrency(invoice.taxTotal)}</span>
        </div>
        <div className="flex justify-between text-lg font-bold text-gray-50 pt-2 border-t border-gray-700">
          <span>TOTAL</span>
          <span className="text-violet-400">{formatCurrency(invoice.total)}</span>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 bg-gray-950/50 border-t border-gray-800 space-y-2">
        {invoice.paymentTerms && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase mb-0.5">Payment terms</p>
            <p className="text-sm text-gray-400">{invoice.paymentTerms}</p>
          </div>
        )}
        {invoice.notes && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase mb-0.5">Notes</p>
            <p className="text-sm text-gray-400">{invoice.notes}</p>
          </div>
        )}
      </div>
    </div>
  );
};
