import React, { useMemo } from 'react';
import { Modal } from '@/components/ui';
import type { AuditEntry } from '@/types/admin';

interface AuditDiffModalProps {
  entry: AuditEntry;
  open: boolean;
  onClose: () => void;
}

interface DiffField {
  key: string;
  before: unknown;
  after: unknown;
  changed: boolean;
}

function computeDiffFields(
  before: Record<string, unknown>,
  after: Record<string, unknown>
): DiffField[] {
  const allKeys = new Set([...Object.keys(before), ...Object.keys(after)]);
  return Array.from(allKeys).map((key) => ({
    key,
    before: before[key],
    after: after[key],
    changed: JSON.stringify(before[key]) !== JSON.stringify(after[key]),
  }));
}

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'object') return JSON.stringify(val, null, 2);
  return String(val);
}

export const AuditDiffModal: React.FC<AuditDiffModalProps> = ({
  entry,
  open,
  onClose,
}) => {
  const fields = useMemo(() => {
    if (!entry.diff) return [];
    return computeDiffFields(entry.diff.before, entry.diff.after);
  }, [entry.diff]);

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Changes — ${entry.action}`}
      size="lg"
    >
      <div className="space-y-3">
        {/* Meta info */}
        <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-4">
          <span>Actor: <span className="text-gray-300">{entry.actor}</span></span>
          <span>Entity: <span className="text-gray-300">{entry.entityType}</span></span>
          <span>ID: <span className="text-gray-300">{entry.entityId}</span></span>
        </div>

        {/* Diff table */}
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <div className="grid grid-cols-3 bg-gray-800/50 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            <div className="px-4 py-2">Field</div>
            <div className="px-4 py-2">Before</div>
            <div className="px-4 py-2">After</div>
          </div>
          {fields.map((f) => (
            <div
              key={f.key}
              className={`grid grid-cols-3 border-t border-gray-800/50 text-sm ${
                f.changed ? 'bg-amber-500/5' : ''
              }`}
            >
              <div className="px-4 py-2.5 font-medium text-gray-300">
                {f.key}
                {f.changed && (
                  <span className="ml-1.5 inline-block h-1.5 w-1.5 rounded-full bg-amber-400" />
                )}
              </div>
              <div
                className={`px-4 py-2.5 font-mono text-xs break-all ${
                  f.changed ? 'text-red-400/80' : 'text-gray-500'
                }`}
              >
                {formatValue(f.before)}
              </div>
              <div
                className={`px-4 py-2.5 font-mono text-xs break-all ${
                  f.changed ? 'text-emerald-400' : 'text-gray-500'
                }`}
              >
                {formatValue(f.after)}
              </div>
            </div>
          ))}
          {fields.length === 0 && (
            <div className="px-4 py-6 text-center text-sm text-gray-500">
              No diff data available
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
};
