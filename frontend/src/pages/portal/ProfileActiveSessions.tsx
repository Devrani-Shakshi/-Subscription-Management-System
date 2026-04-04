import React from 'react';
import { Monitor, LogOut, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui';
import { useActiveSessions, useRevokeSession, useRevokeAllSessions } from '@/hooks/usePortal';
import { formatRelativeTime } from '@/lib/utils';
import type { ActiveSession } from '@/types/portal';

export const ActiveSessionsSection: React.FC = () => {
  const { data: sessions, isLoading } = useActiveSessions();
  const revoke = useRevokeSession();
  const revokeAll = useRevokeAllSessions();

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-200">Active Sessions</h3>
        {sessions && sessions.length > 1 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => revokeAll.mutate()}
            loading={revokeAll.isPending}
            icon={<LogOut className="h-3.5 w-3.5" />}
          >
            Logout all other devices
          </Button>
        )}
      </div>

      <div className="divide-y divide-gray-800/50">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-gray-500" />
          </div>
        ) : !sessions || sessions.length === 0 ? (
          <p className="px-5 py-6 text-sm text-gray-500">No active sessions found.</p>
        ) : (
          sessions.map((session) => (
            <SessionRow
              key={session.id}
              session={session}
              onRevoke={() => revoke.mutate(session.id)}
              isRevoking={revoke.isPending}
            />
          ))
        )}
      </div>
    </div>
  );
};

/* ── Session Row ─────────────────────────────────── */

interface SessionRowProps {
  session: ActiveSession;
  onRevoke: () => void;
  isRevoking: boolean;
}

const SessionRow: React.FC<SessionRowProps> = ({ session, onRevoke, isRevoking }) => {
  return (
    <div className="px-5 py-3.5 flex items-center justify-between gap-3">
      <div className="flex items-center gap-3 min-w-0">
        <div className="h-9 w-9 rounded-lg bg-gray-800 flex items-center justify-center shrink-0">
          <Monitor className="h-4 w-4 text-gray-400" />
        </div>
        <div className="min-w-0">
          <p className="text-sm text-gray-200 truncate">
            {session.device}
            {session.isCurrent && (
              <span className="ml-2 text-xs text-emerald-400 font-medium">(this device)</span>
            )}
          </p>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>{session.ip}</span>
            <span>·</span>
            <span>{formatRelativeTime(session.lastActive)}</span>
          </div>
        </div>
      </div>

      {!session.isCurrent && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onRevoke}
          loading={isRevoking}
          className="text-red-400 hover:text-red-300 shrink-0"
        >
          Revoke
        </Button>
      )}
    </div>
  );
};
