import React from 'react';
import { formatCurrency } from '@/lib/utils';
import type { RevenueTimelinePoint } from '@/types/billing';

interface RevenueTableProps {
  data: RevenueTimelinePoint[];
}

export const RevenueTable: React.FC<RevenueTableProps> = ({ data }) => {
  const totals = data.reduce(
    (acc, row) => ({
      recognized: acc.recognized + row.recognized,
      deferred: acc.deferred + row.deferred,
      newInvoices: acc.newInvoices + row.newInvoices,
      cumulative: row.cumulative, // last value is the cumulative total
    }),
    { recognized: 0, deferred: 0, newInvoices: 0, cumulative: 0 }
  );

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-800">
        <h3 className="text-sm font-semibold text-gray-300">Month-by-month breakdown</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Month</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Recognized</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Deferred</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">New invoices</th>
              <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Cumulative</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.month} className="border-b border-gray-800/30 hover:bg-gray-800/20 transition-colors">
                <td className="px-6 py-3 text-gray-200 font-medium">{row.month}</td>
                <td className="text-right px-4 py-3 text-violet-400">{formatCurrency(row.recognized)}</td>
                <td className="text-right px-4 py-3 text-teal-400">{formatCurrency(row.deferred)}</td>
                <td className="text-right px-4 py-3 text-gray-300">{row.newInvoices}</td>
                <td className="text-right px-6 py-3 text-amber-400">{formatCurrency(row.cumulative)}</td>
              </tr>
            ))}
            {/* Totals row */}
            <tr className="bg-gray-800/30 border-t border-gray-700">
              <td className="px-6 py-3 text-gray-100 font-bold">Totals</td>
              <td className="text-right px-4 py-3 text-violet-300 font-bold">{formatCurrency(totals.recognized)}</td>
              <td className="text-right px-4 py-3 text-teal-300 font-bold">{formatCurrency(totals.deferred)}</td>
              <td className="text-right px-4 py-3 text-gray-200 font-bold">{totals.newInvoices}</td>
              <td className="text-right px-6 py-3 text-amber-300 font-bold">{formatCurrency(totals.cumulative)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
