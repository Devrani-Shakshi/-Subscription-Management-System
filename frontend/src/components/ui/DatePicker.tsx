import React from 'react';
import { Calendar } from 'lucide-react';

interface DatePickerProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const DatePicker = React.forwardRef<HTMLInputElement, DatePickerProps>(
  ({ className = '', error, ...props }, ref) => {
    return (
      <div className="relative">
        <input
          ref={ref}
          type="date"
          className={`
            w-full bg-gray-800 border rounded-lg px-3 py-2 pl-10 text-sm text-gray-100
            transition-colors duration-200
            focus:outline-none focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500
            disabled:opacity-50 disabled:cursor-not-allowed
            [&::-webkit-calendar-picker-indicator]:opacity-0
            [&::-webkit-calendar-picker-indicator]:absolute
            [&::-webkit-calendar-picker-indicator]:inset-0
            [&::-webkit-calendar-picker-indicator]:w-full
            [&::-webkit-calendar-picker-indicator]:h-full
            [&::-webkit-calendar-picker-indicator]:cursor-pointer
            ${error ? 'border-red-500/50 focus:border-red-500 focus:ring-red-500/40' : 'border-gray-700'}
            ${className}
          `.trim()}
          {...props}
        />
        <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500 pointer-events-none" />
      </div>
    );
  }
);

DatePicker.displayName = 'DatePicker';
