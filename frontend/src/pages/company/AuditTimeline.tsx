import React from 'react';
import { formatRelativeTime, formatDate } from '@/lib/utils';
import type { AuditLogEntry, AuditAction } from '@/types/company';

interface AuditTimelineProps {
  entries: AuditLogEntry[];
  onViewDiff: (entry: AuditLogEntry) => void;
}

function groupByDate(entries: AuditLogEntry[]): Map<string, AuditLogEntry[]> {
  const groups = new Map<string, AuditLogEntry[]>();
  const now = new Date();
  const today = now.toDateString();
  const yesterday = new Date(now.getTime() - 86400000).toDateString();

  for (const entry of entries) {
    const d = new Date(entry.created_at);
    let label: string;
    if (d.toDateString() === today) label = 'Today';
    else if (d.toDateString() === yesterday) label = 'Yesterday';
    else label = formatDate(entry.created_at);

    const existing = groups.get(label) ?? [];
    existing.push(entry);
    groups.set(label, existing);
  }
  return groups;
}

const ACTION_COLORS: Record<AuditAction, string> = {
  create: 'bg-emerald-400',
  update: 'bg-amber-400',
  delete: 'bg-red-400',
  status_change: 'bg-blue-400',
};

function describeAction(entry: AuditLogEntry): string {
  const actor = entry.actor_name ?? entry.actor_role;
  const action = entry.action.replace(/_/g, ' ');
  const entity = entry.entity_type;
  return `${actor} ${action}d ${entity}`;
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({
  entries,
  onViewDiff,
}) => {
  if (entries.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No audit entries found
      </div>
    );
  }

  const groups = groupByDate(entries);

  return (
    <div className="space-y-6">
      {Array.from(groups.entries()).map(([dateLabel, items]) => (
        <div key={dateLabel}>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3 px-1">
            {dateLabel}
          </h3>
          <div className="space-y-1">
            {items.map((entry) => (
              <div
                key={entry.id}
                className="flex items-start gap-3 px-4 py-3 rounded-lg
                           hover:bg-gray-900/60 transition-colors group"
              >
                {/* Dot */}
                <span
                  className={`mt-1.5 h-2.5 w-2.5 rounded-full shrink-0 ${
                    ACTION_COLORS[entry.action] ?? 'bg-gray-500'
                  }`}
                />

                {/* Avatar */}
                <div className="h-7 w-7 rounded-full bg-gray-800 flex items-center justify-center
                                text-[10px] font-semibold text-gray-400 shrink-0">
                  {(entry.actor_name ?? 'S').charAt(0).toUpperCase()}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-200">
                    {describeAction(entry)}
                  </p>
                  {Object.keys(entry.diff_json).length > 0 && (
                    <button
                      onClick={() => onViewDiff(entry)}
                      className="text-xs text-violet-400 hover:text-violet-300
                                 opacity-0 group-hover:opacity-100 transition-opacity mt-0.5"
                    >
                      View changes
                    </button>
                  )}
                </div>

                {/* Timestamp */}
                <span className="text-xs text-gray-500 shrink-0 tabular-nums">
                  {formatRelativeTime(entry.created_at)}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
