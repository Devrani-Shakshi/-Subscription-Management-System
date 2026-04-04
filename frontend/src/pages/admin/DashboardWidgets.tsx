import React from 'react';
import { AlertTriangle, Clock, Ban, Eye } from 'lucide-react';
import { StatusBadge, Button } from '@/components/ui';
import { formatCurrency } from '@/lib/utils';
import type { AdminAlert, AdminCompanySummary } from '@/types/admin';
import type { Column } from '@/types';

// ─── Alert Card ───────────────────────────────────────────────────
const ALERT_ICONS: Record<string, React.ReactNode> = {
  trial_expiring: <Clock className="h-4 w-4" />,
  suspended: <Ban className="h-4 w-4" />,
  dunning: <AlertTriangle className="h-4 w-4" />,
};

const ALERT_COLORS: Record<string, string> = {
  high: 'border-red-500/30 bg-red-500/5',
  medium: 'border-amber-500/30 bg-amber-500/5',
  low: 'border-blue-500/30 bg-blue-500/5',
};

const ALERT_ICON_COLORS: Record<string, string> = {
  high: 'text-red-400',
  medium: 'text-amber-400',
  low: 'text-blue-400',
};

interface AlertCardProps {
  alert: AdminAlert;
  onView: (id: string) => void;
}

export const AlertCard: React.FC<AlertCardProps> = ({ alert, onView }) => (
  <div
    className={`min-w-[280px] sm:min-w-[300px] flex-shrink-0 rounded-xl border p-4
      ${ALERT_COLORS[alert.severity]} transition-colors`}
  >
    <div className="flex items-start gap-3">
      <div className={`mt-0.5 ${ALERT_ICON_COLORS[alert.severity]}`}>
        {ALERT_ICONS[alert.type]}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-200 truncate">
          {alert.companyName}
        </p>
        <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">
          {alert.message}
        </p>
      </div>
      <button
        onClick={() => onView(alert.companyId)}
        className="shrink-0 text-xs text-violet-400 hover:text-violet-300
          font-medium transition-colors h-8 flex items-center"
      >
        View
      </button>
    </div>
  </div>
);

// ─── Companies Mobile Card ────────────────────────────────────────
interface CompanyCardProps {
  company: AdminCompanySummary;
  onView: (id: string) => void;
}

export const CompanyCard: React.FC<CompanyCardProps> = ({ company, onView }) => (
  <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors">
    <div className="flex items-center gap-3 mb-3">
      <div className="h-10 w-10 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center shrink-0">
        <span className="text-sm font-bold text-violet-400">
          {company.name.charAt(0).toUpperCase()}
        </span>
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-100 truncate">{company.name}</p>
        <p className="text-xs text-gray-500">{company.slug}</p>
      </div>
      <StatusBadge status={company.status} />
    </div>
    <div className="flex items-center justify-between">
      <span className="text-sm font-semibold text-gray-200">
        {formatCurrency(company.mrr)}/mo
      </span>
      <Button variant="ghost" size="sm" onClick={() => onView(company.id)}>
        View
      </Button>
    </div>
  </div>
);

// ─── Companies Table Columns ──────────────────────────────────────
export function getCompanyColumns(
  onView: (id: string) => void
): Column<AdminCompanySummary>[] {
  return [
    {
      key: 'name',
      header: 'Company',
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
            <span className="text-xs font-bold text-violet-400">
              {row.name.charAt(0).toUpperCase()}
            </span>
          </div>
          <span className="font-medium">{row.name}</span>
        </div>
      ),
    },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} /> },
    { key: 'mrr', header: 'MRR', sortable: true, render: (row) => formatCurrency(row.mrr) },
    { key: 'activeSubs', header: 'Active Subs', sortable: true },
    {
      key: 'trialEnds',
      header: 'Trial Ends',
      render: (row) =>
        row.trialEnds ? new Date(row.trialEnds).toLocaleDateString() : '—',
    },
    {
      key: 'actions',
      header: '',
      width: '80px',
      render: (row) => (
        <Button variant="ghost" size="sm" icon={<Eye className="h-3.5 w-3.5" />} onClick={() => onView(row.id)}>
          View
        </Button>
      ),
    },
  ];
}
