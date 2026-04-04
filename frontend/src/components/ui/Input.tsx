import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', error, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={`
          w-full bg-gray-800 border rounded-lg px-3 py-2 text-sm text-gray-100
          placeholder:text-gray-500
          transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500
          disabled:opacity-50 disabled:cursor-not-allowed
          ${error ? 'border-red-500/50 focus:border-red-500 focus:ring-red-500/40' : 'border-gray-700'}
          ${className}
        `.trim()}
        {...props}
      />
    );
  }
);

Input.displayName = 'Input';
