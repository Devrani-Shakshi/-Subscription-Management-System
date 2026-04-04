import React from 'react';

interface WizardProgressProps {
  steps: { label: string; key: string }[];
  current: number;
}

export const WizardProgress: React.FC<WizardProgressProps> = ({
  steps,
  current,
}) => {
  return (
    <div className="flex items-center justify-center gap-2 lg:hidden">
      {steps.map((step, i) => (
        <React.Fragment key={step.key}>
          {i > 0 && (
            <div
              className={`h-px w-6 transition-colors duration-300 ${
                i <= current ? 'bg-violet-500' : 'bg-gray-800'
              }`}
            />
          )}
          <div className="flex flex-col items-center gap-1">
            <div
              className={`
                h-8 w-8 flex items-center justify-center rounded-full text-xs font-bold
                transition-all duration-300
                ${i === current
                  ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/30'
                  : i < current
                    ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-gray-800 text-gray-600 border border-gray-700'
                }
              `.trim()}
            >
              {i < current ? '✓' : i + 1}
            </div>
            <span
              className={`text-[10px] font-medium transition-colors ${
                i === current ? 'text-violet-400' : 'text-gray-600'
              }`}
            >
              {step.label}
            </span>
          </div>
        </React.Fragment>
      ))}
    </div>
  );
};
