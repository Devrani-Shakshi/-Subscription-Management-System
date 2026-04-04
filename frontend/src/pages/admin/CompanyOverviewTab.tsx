import React from 'react';
import { StatusBadge } from '@/components/ui';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { AdminCompanyDetail } from '@/types/admin';

interface CompanyOverviewTabProps {
  company: AdminCompanyDetail;
}

export const CompanyOverviewTab: React.FC<CompanyOverviewTabProps> = ({
  company,
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Company Info */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Company Information
        </h3>
        <dl className="space-y-3">
          <InfoRow label="Name" value={company.name} />
          <InfoRow label="Slug" value={company.slug} />
          <InfoRow
            label="Status"
            value={<StatusBadge status={company.status} />}
          />
          <InfoRow label="Owner" value={company.ownerEmail} />
          <InfoRow label="Created" value={formatDate(company.createdAt)} />
          {company.trialEnds && (
            <InfoRow
              label="Trial Ends"
              value={formatDate(company.trialEnds)}
            />
          )}
        </dl>
      </div>

      {/* Metrics */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Metrics
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <MetricCard label="MRR" value={formatCurrency(company.mrr)} />
          <MetricCard
            label="Active Subs"
            value={company.activeSubs.toString()}
          />
          <MetricCard
            label="Total Customers"
            value={company.totalCustomers.toString()}
          />
          <MetricCard
            label="Total Invoices"
            value={company.totalInvoices.toString()}
          />
        </div>
      </div>
    </div>
  );
};

// ─── Sub-components ───────────────────────────────────────────────
interface InfoRowProps {
  label: string;
  value: React.ReactNode;
}

const InfoRow: React.FC<InfoRowProps> = ({ label, value }) => (
  <div className="flex items-center justify-between py-1.5 border-b border-gray-800/50 last:border-0">
    <dt className="text-sm text-gray-500">{label}</dt>
    <dd className="text-sm text-gray-200 font-medium">{value}</dd>
  </div>
);

interface MetricCardProps {
  label: string;
  value: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value }) => (
  <div className="bg-gray-800/50 rounded-lg p-3 text-center">
    <p className="text-xs text-gray-500 mb-1">{label}</p>
    <p className="text-lg font-bold text-gray-100">{value}</p>
  </div>
);
