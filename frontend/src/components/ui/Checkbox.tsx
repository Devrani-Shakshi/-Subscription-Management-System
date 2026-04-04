import React from 'react';
import { Check } from 'lucide-react';

interface CheckboxProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: boolean;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, className = '', error, id, ...props }, ref) => {
    const inputId = id || props.name || 'checkbox';

    return (
      <label
        htmlFor={inputId}
        className={`inline-flex items-center gap-2.5 cursor-pointer select-none group ${className}`}
      >
        <div className="relative">
          <input
            ref={ref}
            type="checkbox"
            id={inputId}
            className="peer sr-only"
            {...props}
          />
          <div
            className={`
              h-5 w-5 rounded-md border-2 transition-all duration-200
              flex items-center justify-center
              peer-checked:bg-violet-600 peer-checked:border-violet-600
              peer-focus-visible:ring-2 peer-focus-visible:ring-violet-500/40 peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-gray-950
              group-hover:border-gray-500
              ${error ? 'border-red-500/50' : 'border-gray-600'}
            `.trim()}
          >
            <Check className="h-3 w-3 text-white opacity-0 peer-checked:opacity-100 transition-opacity" />
          </div>
        </div>
        {label && (
          <span className="text-sm text-gray-300 group-hover:text-gray-100 transition-colors">
            {label}
          </span>
        )}
      </label>
    );
  }
);

Checkbox.displayName = 'Checkbox';
