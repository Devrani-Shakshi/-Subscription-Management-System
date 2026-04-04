import React from 'react';
import { CreditCard, Clock } from 'lucide-react';
import { StatusBadge } from '@/components/ui';
import { formatCurrency, formatDate, formatRelativeTime } from '@/lib/utils';
import type { InvoicePaymentRecord, InvoiceAuditEntry } from '@/types/billing';

/* ── Payment History ──────────────────────────────── */

interface PaymentHistoryProps {
  payments: InvoicePaymentRecord[];
}

export const PaymentHistoryCard: React.FC<PaymentHistoryProps> = ({ payments }) => {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
        <CreditCard className="h-4 w-4 text-teal-400" />
        Payment history
      </h3>

      {payments.length === 0 ? (
        <p className="text-sm text-gray-500">No payments recorded</p>
      ) : (
        <div className="space-y-3">
          {payments.map((p) => (
            <div key={p.id} className="flex items-center justify-between p-3 bg-gray-800/40 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-200">
                  {formatCurrency(p.amount)}
                </p>
                <p className="text-xs text-gray-500">{formatDate(p.date)}</p>
              </div>
              <StatusBadge status={p.method.replace('_', ' ')} variant="info" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

/* ── Audit Timeline ───────────────────────────────── */

interface AuditTimelineProps {
  entries: InvoiceAuditEntry[];
}

export const AuditTimelineCard: React.FC<AuditTimelineProps> = ({ entries }) => {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
        <Clock className="h-4 w-4 text-violet-400" />
        Audit timeline
      </h3>

      {entries.length === 0 ? (
        <p className="text-sm text-gray-500">No activity yet</p>
      ) : (
        <div className="relative space-y-0">
          {/* Vertical line */}
          <div className="absolute left-[7px] top-3 bottom-3 w-px bg-gray-800" />

          {entries.map((entry, i) => (
            <div key={entry.id} className="relative flex gap-3 pb-4 last:pb-0">
              <div className={`
                relative z-10 mt-1 h-3.5 w-3.5 rounded-full border-2 shrink-0
                ${i === 0 ? 'border-violet-500 bg-violet-500/20' : 'border-gray-700 bg-gray-900'}
              `.trim()} />
              <div className="min-w-0 flex-1">
                <p className="text-sm text-gray-200">{entry.action}</p>
                <p className="text-xs text-gray-500">
                  {entry.user} · {formatRelativeTime(entry.timestamp)}
                </p>
                {entry.details && (
                  <p className="text-xs text-gray-600 mt-0.5">{entry.details}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
