import React from 'react';
import { StatusBadge, Button } from '@/components/ui';
import { formatDate } from '@/lib/utils';
import type { AuditEntry } from '@/types/admin';
import type { Column, FilterConfig } from '@/types';

export const AUDIT_FILTER_CONFIGS: FilterConfig[] = [
  {
    key: 'entityType',
    label: 'Entity Type',
    type: 'select',
    options: [
      { label: 'Company', value: 'company' },
      { label: 'Subscription', value: 'subscription' },
      { label: 'Customer', value: 'customer' },
      { label: 'Invoice', value: 'invoice' },
      { label: 'Plan', value: 'plan' },
      { label: 'User', value: 'user' },
    ],
  },
  {
    key: 'action',
    label: 'Action',
    type: 'select',
    options: [
      { label: 'Create', value: 'create' },
      { label: 'Update', value: 'update' },
      { label: 'Delete', value: 'delete' },
      { label: 'Suspend', value: 'suspend' },
      { label: 'Reactivate', value: 'reactivate' },
    ],
  },
  { key: 'actor', label: 'Actor', type: 'search' },
  { key: 'dateFrom', label: 'From', type: 'date' },
  { key: 'dateTo', label: 'To', type: 'date' },
];

export function getAuditColumns(
  onViewDiff: (entry: AuditEntry) => void
): Column<AuditEntry>[] {
  return [
    { key: 'actor', header: 'Actor', sortable: true },
    { key: 'actorRole', header: 'Role' },
    { key: 'companyName', header: 'Company', sortable: true },
    { key: 'entityType', header: 'Entity' },
    { key: 'entityId', header: 'Entity ID' },
    { key: 'action', header: 'Action' },
    { key: 'timestamp', header: 'Date', sortable: true, render: (row) => formatDate(row.timestamp) },
    {
      key: 'diff',
      header: '',
      width: '120px',
      render: (row) =>
        row.diff ? (
          <Button variant="ghost" size="sm" onClick={() => onViewDiff(row)}>
            View changes
          </Button>
        ) : (
          <span className="text-xs text-gray-600">—</span>
        ),
    },
  ];
}
