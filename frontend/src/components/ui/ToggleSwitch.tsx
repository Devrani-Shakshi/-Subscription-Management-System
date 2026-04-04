import React from 'react';

interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  description?: string;
  disabled?: boolean;
  className?: string;
}

export const ToggleSwitch: React.FC<ToggleSwitchProps> = ({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  className = '',
}) => {
  return (
    <label
      className={`flex items-start gap-3 cursor-pointer select-none group ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      } ${className}`}
    >
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`
          relative mt-0.5 h-6 w-11 shrink-0 rounded-full
          transition-colors duration-200 ease-in-out
          focus-visible:outline-none focus-visible:ring-2
          focus-visible:ring-violet-500 focus-visible:ring-offset-2
          focus-visible:ring-offset-gray-950
          ${checked ? 'bg-violet-600' : 'bg-gray-700'}
        `.trim()}
      >
        <span
          className={`
            absolute top-0.5 left-0.5 h-5 w-5 rounded-full
            bg-white shadow-sm transition-transform duration-200
            ${checked ? 'translate-x-5' : 'translate-x-0'}
          `.trim()}
        />
      </button>
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-200 group-hover:text-gray-100 transition-colors">
          {label}
        </p>
        {description && (
          <p className="text-xs text-gray-500 mt-0.5">{description}</p>
        )}
      </div>
    </label>
  );
};
