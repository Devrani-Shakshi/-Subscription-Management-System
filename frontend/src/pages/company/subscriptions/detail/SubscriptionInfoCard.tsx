import React from 'react';
import { User, CreditCard, Calendar, FileText } from 'lucide-react';
import { StatusBadge } from '@/components/ui';
import { formatDate } from '@/lib/utils';
import type { Subscription } from '@/types/subscription';

interface SubscriptionInfoCardProps {
  subscription: Subscription;
}

const TERMS_LABEL: Record<string, string> = {
  net_7: 'Net 7',
  net_15: 'Net 15',
  net_30: 'Net 30',
  due_on_receipt: 'Due on receipt',
};

export const SubscriptionInfoCard: React.FC<SubscriptionInfoCardProps> = ({
  subscription,
}) => {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
        Subscription Info
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <InfoRow
          icon={<User className="h-4 w-4 text-violet-400" />}
          label="Customer"
          value={subscription.customerName}
          sub={subscription.customerEmail}
        />
        <InfoRow
          icon={<CreditCard className="h-4 w-4 text-teal-400" />}
          label="Plan"
          value={subscription.planName}
        />
        <InfoRow
          icon={<Calendar className="h-4 w-4 text-amber-400" />}
          label="Start Date"
          value={formatDate(subscription.startDate)}
        />
        <InfoRow
          icon={<Calendar className="h-4 w-4 text-rose-400" />}
          label="Expiry Date"
          value={formatDate(subscription.expiryDate)}
        />
        <InfoRow
          icon={<FileText className="h-4 w-4 text-blue-400" />}
          label="Payment Terms"
          value={TERMS_LABEL[subscription.paymentTerms] ?? subscription.paymentTerms}
        />
        <div className="flex items-start gap-3">
          <div className="h-8 w-8 rounded-lg bg-gray-800 flex items-center justify-center shrink-0">
            <StatusBadge status={subscription.status} />
          </div>
        </div>
      </div>

      {subscription.notes && (
        <div className="pt-3 border-t border-gray-800">
          <p className="text-xs text-gray-500 mb-1">Notes</p>
          <p className="text-sm text-gray-300 whitespace-pre-wrap">
            {subscription.notes}
          </p>
        </div>
      )}
    </div>
  );
};

interface InfoRowProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
}

const InfoRow: React.FC<InfoRowProps> = ({ icon, label, value, sub }) => (
  <div className="flex items-start gap-3">
    <div className="h-8 w-8 rounded-lg bg-gray-800 flex items-center justify-center shrink-0">
      {icon}
    </div>
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-medium text-gray-100">{value}</p>
      {sub && <p className="text-xs text-gray-500">{sub}</p>}
    </div>
  </div>
);
