import React from 'react';

interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = '', error, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={`
          w-full bg-gray-800 border rounded-lg px-3 py-2 text-sm text-gray-100
          placeholder:text-gray-500 min-h-[5rem] resize-y
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

Textarea.displayName = 'Textarea';
