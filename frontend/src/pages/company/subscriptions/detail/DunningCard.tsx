import React from 'react';
import { AlertOctagon, Clock } from 'lucide-react';
import { useDunningInfo } from '@/hooks/useSubscriptions';
import { formatDate } from '@/lib/utils';

interface DunningCardProps {
  subscriptionId: string;
}

export const DunningCard: React.FC<DunningCardProps> = ({ subscriptionId }) => {
  const { data: dunning } = useDunningInfo(subscriptionId);

  if (!dunning) return null;

  const stepProgress = (dunning.currentStep / dunning.totalSteps) * 100;

  return (
    <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4 space-y-3">
      <div className="flex items-center gap-2">
        <AlertOctagon className="h-4 w-4 text-red-400" />
        <h3 className="text-sm font-semibold text-red-400">Active Dunning</h3>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <p className="text-gray-500">Step</p>
          <p className="text-gray-200 font-medium">
            {dunning.currentStep} of {dunning.totalSteps}
          </p>
        </div>
        <div>
          <p className="text-gray-500">Failed Attempts</p>
          <p className="text-red-400 font-medium">{dunning.failedAttempts}</p>
        </div>
      </div>

      {/* Step progress */}
      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-red-500 rounded-full transition-all duration-500"
          style={{ width: `${stepProgress}%` }}
        />
      </div>

      <div className="flex items-center gap-1.5 text-xs text-gray-400">
        <Clock className="h-3 w-3" />
        Next attempt: {formatDate(dunning.nextAttempt)}
      </div>
    </div>
  );
};
