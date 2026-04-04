import React from 'react';
import { Modal } from './Modal';
import type { DiffField } from '@/types/company';

interface DiffModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  diff: Record<string, DiffField>;
}

export const DiffModal: React.FC<DiffModalProps> = ({
  open,
  onClose,
  title = 'View changes',
  diff,
}) => {
  const fields = Object.entries(diff);

  return (
    <Modal open={open} onClose={onClose} title={title} size="lg">
      {fields.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-6">No changes recorded.</p>
      ) : (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3 text-xs font-semibold text-gray-400 uppercase tracking-wider px-1">
            <span>Before</span>
            <span>After</span>
          </div>
          {fields.map(([key, val]) => (
            <div key={key} className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {/* Before */}
              <div className="bg-red-500/5 border border-red-500/10 rounded-lg p-3">
                <span className="block text-[10px] uppercase tracking-wider text-gray-500 mb-1 font-mono">
                  {key}
                </span>
                <span className="text-sm text-red-400 line-through">
                  {val.old === null ? '—' : String(val.old)}
                </span>
              </div>
              {/* After */}
              <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-lg p-3">
                <span className="block text-[10px] uppercase tracking-wider text-gray-500 mb-1 font-mono">
                  {key}
                </span>
                <span className="text-sm text-emerald-400 font-medium">
                  {val.new === null ? '—' : String(val.new)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Modal>
  );
};
