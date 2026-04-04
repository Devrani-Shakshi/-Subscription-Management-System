import React from 'react';

interface ScoreBarProps {
  score: number;
  className?: string;
}

function getScoreColor(score: number): string {
  if (score >= 70) return 'bg-red-500';
  if (score >= 30) return 'bg-amber-500';
  return 'bg-emerald-500';
}

function getScoreLabel(score: number): string {
  if (score >= 70) return 'text-red-400';
  if (score >= 30) return 'text-amber-400';
  return 'text-emerald-400';
}

export const ScoreBar: React.FC<ScoreBarProps> = ({ score, className = '' }) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden min-w-[60px]">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getScoreColor(score)}`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
      <span className={`text-xs font-semibold tabular-nums ${getScoreLabel(score)}`}>
        {score}
      </span>
    </div>
  );
};
