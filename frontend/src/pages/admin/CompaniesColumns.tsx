import React from 'react';
import { Eye, Pause, Play, Trash2 } from 'lucide-react';
import { StatusBadge, Button } from '@/components/ui';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { AdminCompanySummary } from '@/types/admin';
import type { Column } from '@/types';

export function getCompaniesColumns(
  onView: (id: string) => void,
  onSuspend: (c: AdminCompanySummary) => void,
  onDelete: (c: AdminCompanySummary) => void
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
          <div>
            <p className="font-medium">{row.name}</p>
            <p className="text-xs text-gray-500">{row.slug}</p>
          </div>
        </div>
      ),
    },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} /> },
    { key: 'mrr', header: 'MRR', sortable: true, render: (row) => formatCurrency(row.mrr) },
    { key: 'activeSubs', header: 'Subs', sortable: true },
    { key: 'trialEnds', header: 'Trial Ends', render: (row) => (row.trialEnds ? formatDate(row.trialEnds) : '—') },
    { key: 'createdAt', header: 'Created', render: (row) => formatDate(row.createdAt) },
    {
      key: 'actions',
      header: '',
      width: '160px',
      render: (row) => (
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" icon={<Eye className="h-3.5 w-3.5" />} onClick={() => onView(row.id)}>
            View
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={row.status === 'suspended' ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
            onClick={() => onSuspend(row)}
          />
          <Button variant="ghost" size="sm" icon={<Trash2 className="h-3.5 w-3.5 text-red-400" />} onClick={() => onDelete(row)} />
        </div>
      ),
    },
  ];
}
