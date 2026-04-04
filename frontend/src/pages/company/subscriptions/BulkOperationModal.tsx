import React, { useState, useCallback, useMemo } from 'react';
import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import { Modal, Button } from '@/components/ui';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import {
  useBulkConflicts,
  useBulkExecute,
  useBulkJobStatus,
} from '@/hooks/useSubscriptions';
import type { BulkAction, BulkConflict } from '@/types/subscription';

interface BulkOperationModalProps {
  selectedIds: string[];
  action: BulkAction;
  onClose: () => void;
  onComplete: () => void;
}

const ACTION_LABELS: Record<BulkAction, string> = {
  activate: 'Activate',
  close: 'Close',
  apply_discount: 'Apply Discount',
};

export const BulkOperationModal: React.FC<BulkOperationModalProps> = ({
  selectedIds,
  action,
  onClose,
  onComplete,
}) => {
  const { isMobile } = useBreakpoint();
  const [step, setStep] = useState(0);
  const [skippedIds, setSkippedIds] = useState<Set<string>>(new Set());
  const [jobId, setJobId] = useState<string | null>(null);

  const { data: conflicts, isLoading: conflictsLoading } = useBulkConflicts(
    step === 1 ? selectedIds : [],
    action
  );
  const executeMutation = useBulkExecute();
  const { data: jobStatus } = useBulkJobStatus(jobId);

  const nonConflictedIds = useMemo(() => {
    if (!conflicts) return selectedIds;
    const conflictIds = new Set(conflicts.map((c) => c.id));
    return selectedIds.filter(
      (id) => !conflictIds.has(id) || skippedIds.has(id) === false
    );
  }, [selectedIds, conflicts, skippedIds]);

  const toggleSkip = useCallback((id: string) => {
    setSkippedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleConfirm = useCallback(() => {
    setStep(1);
  }, []);

  const handleProceed = useCallback(async () => {
    setStep(2);
    const finalIds = conflicts
      ? selectedIds.filter(
          (id) =>
            !conflicts.find((c) => c.id === id) || !skippedIds.has(id)
        )
      : selectedIds;

    const result = await executeMutation.mutateAsync({
      ids: finalIds,
      action,
    });
    setJobId(result.jobId);
  }, [selectedIds, conflicts, skippedIds, executeMutation, action]);

  const isCompleted = jobStatus?.status === 'completed' || jobStatus?.status === 'failed';

  return (
    <Modal
      open
      onClose={isCompleted ? onComplete : onClose}
      title={`Bulk ${ACTION_LABELS[action]}`}
      size={isMobile ? 'md' : 'lg'}
    >
      {/* Step 0: Confirm */}
      {step === 0 && (
        <StepConfirm
          count={selectedIds.length}
          action={ACTION_LABELS[action]}
          onConfirm={handleConfirm}
          onCancel={onClose}
        />
      )}

      {/* Step 1: Conflicts */}
      {step === 1 && (
        <StepConflicts
          loading={conflictsLoading}
          conflicts={conflicts ?? []}
          skippedIds={skippedIds}
          toggleSkip={toggleSkip}
          nonConflictedCount={nonConflictedIds.length}
          onProceed={handleProceed}
          onCancel={onClose}
          executing={executeMutation.isPending}
        />
      )}

      {/* Step 2: Progress */}
      {step === 2 && (
        <StepProgress
          jobStatus={jobStatus ?? null}
          onDone={onComplete}
        />
      )}
    </Modal>
  );
};

/* ── Sub-components ────────────────────────────────────────────── */

interface StepConfirmProps {
  count: number;
  action: string;
  onConfirm: () => void;
  onCancel: () => void;
}

const StepConfirm: React.FC<StepConfirmProps> = ({
  count,
  action,
  onConfirm,
  onCancel,
}) => (
  <div className="space-y-6">
    <div className="flex items-center gap-3 p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
      <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
      <p className="text-sm text-amber-200">
        You are about to <strong>{action.toLowerCase()}</strong>{' '}
        <strong>{count}</strong> subscription{count !== 1 ? 's' : ''}.
      </p>
    </div>
    <div className="flex justify-end gap-3">
      <Button variant="ghost" onClick={onCancel}>Cancel</Button>
      <Button variant="primary" onClick={onConfirm}>Check conflicts</Button>
    </div>
  </div>
);

interface StepConflictsProps {
  loading: boolean;
  conflicts: BulkConflict[];
  skippedIds: Set<string>;
  toggleSkip: (id: string) => void;
  nonConflictedCount: number;
  onProceed: () => void;
  onCancel: () => void;
  executing: boolean;
}

const StepConflicts: React.FC<StepConflictsProps> = ({
  loading,
  conflicts,
  skippedIds,
  toggleSkip,
  nonConflictedCount,
  onProceed,
  onCancel,
  executing,
}) => (
  <div className="space-y-4">
    {loading ? (
      <div className="flex justify-center py-8">
        <div className="h-8 w-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
      </div>
    ) : conflicts.length === 0 ? (
      <div className="flex items-center gap-3 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
        <CheckCircle2 className="h-5 w-5 text-emerald-400" />
        <p className="text-sm text-emerald-200">No conflicts found. Ready to proceed.</p>
      </div>
    ) : (
      <>
        <p className="text-sm text-gray-300">
          {conflicts.length} conflict{conflicts.length !== 1 ? 's' : ''} found:
        </p>
        <div className="max-h-60 overflow-y-auto space-y-2">
          {conflicts.map((c) => (
            <div
              key={c.id}
              className="flex items-center justify-between gap-3 p-3 rounded-lg
                         bg-gray-800/50 border border-gray-800"
            >
              <div className="min-w-0">
                <span className="font-mono text-xs text-gray-400">{c.number}</span>
                <p className="text-xs text-red-400 mt-0.5">{c.reason}</p>
              </div>
              <label className="flex items-center gap-2 shrink-0 cursor-pointer">
                <span className="text-xs text-gray-500">Skip</span>
                <input
                  type="checkbox"
                  checked={skippedIds.has(c.id)}
                  onChange={() => toggleSkip(c.id)}
                  className="h-4 w-4 rounded border-gray-600 bg-gray-800 text-violet-500
                             focus:ring-violet-500/40"
                />
              </label>
            </div>
          ))}
        </div>
      </>
    )}
    <div className="flex justify-end gap-3 pt-2">
      <Button variant="ghost" onClick={onCancel} disabled={executing}>Cancel</Button>
      <Button
        variant="primary"
        onClick={onProceed}
        loading={executing}
        disabled={nonConflictedCount === 0}
      >
        Proceed ({nonConflictedCount})
      </Button>
    </div>
  </div>
);

interface StepProgressProps {
  jobStatus: import('@/types/subscription').BulkJobStatus | null;
  onDone: () => void;
}

const StepProgress: React.FC<StepProgressProps> = ({ jobStatus, onDone }) => {
  const isFinished = jobStatus?.status === 'completed' || jobStatus?.status === 'failed';
  const progress = jobStatus?.progress ?? 0;

  return (
    <div className="space-y-6">
      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Processing…</span>
          <span className="text-gray-200 font-medium">{Math.round(progress)}%</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-violet-600 to-violet-400 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {isFinished && jobStatus && (
        <div className="space-y-3">
          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
              {jobStatus.succeeded} succeeded
            </span>
            {jobStatus.failed > 0 && (
              <span className="flex items-center gap-1.5 text-red-400">
                <XCircle className="h-4 w-4" />
                {jobStatus.failed} failed
              </span>
            )}
          </div>

          {jobStatus.failures.length > 0 && (
            <div className="max-h-32 overflow-y-auto space-y-1">
              {jobStatus.failures.map((f) => (
                <p key={f.id} className="text-xs text-red-400">
                  {f.id}: {f.reason}
                </p>
              ))}
            </div>
          )}

          <div className="flex justify-end">
            <Button variant="primary" onClick={onDone}>Done</Button>
          </div>
        </div>
      )}
    </div>
  );
};
