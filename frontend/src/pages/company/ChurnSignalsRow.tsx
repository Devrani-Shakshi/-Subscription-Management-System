import React from 'react';
import { AlertTriangle, Check } from 'lucide-react';
import type { ChurnSignalDetail } from '@/types/company';

interface ChurnSignalsRowProps {
  signals: ChurnSignalDetail[];
}

export const ChurnSignalsRow: React.FC<ChurnSignalsRowProps> = ({ signals }) => {
  if (signals.length === 0) {
    return <p className="text-xs text-gray-500 py-2">No signals recorded.</p>;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 py-2">
      {signals.map((s) => (
        <div
          key={s.key}
          className={`flex items-start gap-2.5 p-2.5 rounded-lg border transition-colors ${
            s.triggered
              ? 'border-red-500/20 bg-red-500/5'
              : 'border-gray-800 bg-gray-900/30'
          }`}
        >
          {s.triggered ? (
            <AlertTriangle className="h-3.5 w-3.5 text-red-400 shrink-0 mt-0.5" />
          ) : (
            <Check className="h-3.5 w-3.5 text-gray-600 shrink-0 mt-0.5" />
          )}
          <div className="min-w-0 flex-1">
            <p className={`text-xs font-medium ${
              s.triggered ? 'text-red-300' : 'text-gray-500'
            }`}>
              {s.key.replace(/_/g, ' ')}
            </p>
            {s.detail && (
              <p className="text-[10px] text-gray-500 mt-0.5">{s.detail}</p>
            )}
          </div>
          <span className={`text-[10px] font-semibold tabular-nums ${
            s.triggered ? 'text-red-400' : 'text-gray-600'
          }`}>
            w:{s.weight}
          </span>
        </div>
      ))}
    </div>
  );
};
