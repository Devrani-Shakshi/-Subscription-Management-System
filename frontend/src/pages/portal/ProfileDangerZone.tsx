import React from 'react';
import { AlertOctagon, ArrowRight } from 'lucide-react';

interface DangerZoneSectionProps {
  onNavigate: () => void;
}

export const DangerZoneSection: React.FC<DangerZoneSectionProps> = ({ onNavigate }) => {
  return (
    <div className="rounded-xl border border-red-500/20 bg-gray-900/50 overflow-hidden">
      <div className="px-5 py-4 border-b border-red-500/15">
        <h3 className="text-sm font-semibold text-red-400">Danger Zone</h3>
      </div>
      <div className="p-5">
        <button
          onClick={onNavigate}
          className="w-full flex items-center justify-between gap-3 rounded-lg bg-red-500/5 border border-red-500/15 px-4 py-3 hover:bg-red-500/10 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <AlertOctagon className="h-5 w-5 text-red-400 shrink-0" />
            <div className="text-left">
              <p className="text-sm font-medium text-gray-200">Cancel my subscription</p>
              <p className="text-xs text-gray-500 mt-0.5">
                Navigate to your subscription to manage cancellation
              </p>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-gray-600 group-hover:text-red-400 transition-colors shrink-0" />
        </button>
      </div>
    </div>
  );
};
