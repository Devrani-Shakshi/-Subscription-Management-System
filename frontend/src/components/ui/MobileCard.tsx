import React from 'react';

interface MobileCardField {
  label: string;
  value: React.ReactNode;
}

interface MobileCardProps {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  fields: MobileCardField[];
  trailing?: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export const MobileCard: React.FC<MobileCardProps> = ({
  title,
  subtitle,
  fields,
  trailing,
  onClick,
  className = '',
}) => {
  return (
    <div
      onClick={onClick}
      className={`
        bg-gray-900 border border-gray-800 rounded-xl p-4
        transition-colors duration-150
        ${onClick ? 'cursor-pointer hover:bg-gray-800/60 active:scale-[0.99]' : ''}
        ${className}
      `.trim()}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="font-medium text-gray-100 truncate">{title}</div>
          {subtitle && (
            <div className="text-sm text-gray-400 mt-0.5">{subtitle}</div>
          )}
        </div>
        {trailing && (
          <div className="shrink-0">{trailing}</div>
        )}
      </div>

      {fields.length > 0 && (
        <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2">
          {fields.map((field, i) => (
            <div key={i}>
              <p className="text-xs text-gray-500">{field.label}</p>
              <div className="text-sm text-gray-200 mt-0.5">{field.value}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
