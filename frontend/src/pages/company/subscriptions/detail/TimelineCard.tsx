import React from 'react';
import { Clock, ArrowRight } from 'lucide-react';
import { useSubscriptionTimeline } from '@/hooks/useSubscriptions';
import { formatRelativeTime } from '@/lib/utils';
import { StatusBadge } from '@/components/ui';

interface TimelineCardProps {
  subscriptionId: string;
}

export const TimelineCard: React.FC<TimelineCardProps> = ({
  subscriptionId,
}) => {
  const { data: entries, isLoading } = useSubscriptionTimeline(subscriptionId);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-800">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          Activity Timeline
        </h3>
      </div>

      {isLoading ? (
        <div className="p-4 space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-800 rounded animate-pulse" />
          ))}
        </div>
      ) : !entries || entries.length === 0 ? (
        <div className="flex flex-col items-center py-6 text-center">
          <Clock className="h-8 w-8 text-gray-700 mb-2" />
          <p className="text-sm text-gray-500">No activity yet</p>
        </div>
      ) : (
        <div className="p-4 space-y-0">
          {entries.map((entry, i) => (
            <div key={entry.id} className="relative flex gap-3 pb-4 last:pb-0">
              {/* Connector line */}
              {i < entries.length - 1 && (
                <div className="absolute left-[11px] top-6 bottom-0 w-px bg-gray-800" />
              )}

              {/* Dot */}
              <div className="h-6 w-6 rounded-full bg-gray-800 flex items-center justify-center shrink-0 z-10">
                <div className="h-2 w-2 rounded-full bg-violet-400" />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  {entry.fromStatus && (
                    <>
                      <StatusBadge status={entry.fromStatus} />
                      <ArrowRight className="h-3 w-3 text-gray-600" />
                    </>
                  )}
                  <StatusBadge status={entry.toStatus} />
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {entry.actor} · {formatRelativeTime(entry.timestamp)}
                </p>
                {entry.details && (
                  <p className="text-xs text-gray-500 mt-0.5">{entry.details}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
