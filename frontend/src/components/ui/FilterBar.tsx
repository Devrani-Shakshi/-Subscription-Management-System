import React, { useState } from 'react';
import { Filter, X } from 'lucide-react';
import { Select } from './Select';
import { Input } from './Input';
import { DatePicker } from './DatePicker';
import { Drawer } from './Drawer';
import { Button } from './Button';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import type { FilterConfig } from '@/types';

interface FilterBarProps {
  filters: FilterConfig[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
  className?: string;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  values,
  onChange,
  className = '',
}) => {
  const { isMobile } = useBreakpoint();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const activeCount = Object.values(values).filter(Boolean).length;

  const filterFields = (
    <div className={`flex flex-col sm:flex-row gap-3 ${isMobile ? 'p-4' : ''}`}>
      {filters.map((filter) => (
        <div key={filter.key} className="min-w-[160px]">
          <label className="block text-xs font-medium text-gray-400 mb-1">
            {filter.label}
          </label>
          {filter.type === 'select' && filter.options ? (
            <Select
              options={filter.options}
              value={values[filter.key] ?? ''}
              onChange={(e) => onChange(filter.key, e.target.value)}
              placeholder={`All ${filter.label}`}
            />
          ) : filter.type === 'date' ? (
            <DatePicker
              value={values[filter.key] ?? ''}
              onChange={(e) => onChange(filter.key, e.target.value)}
            />
          ) : (
            <Input
              value={values[filter.key] ?? ''}
              onChange={(e) => onChange(filter.key, e.target.value)}
              placeholder={`Search ${filter.label.toLowerCase()}…`}
            />
          )}
        </div>
      ))}
    </div>
  );

  if (isMobile) {
    return (
      <>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setDrawerOpen(true)}
          icon={<Filter className="h-4 w-4" />}
          className={className}
        >
          Filters
          {activeCount > 0 && (
            <span className="ml-1.5 h-5 min-w-[1.25rem] flex items-center justify-center rounded-full bg-violet-600 text-xs text-white px-1">
              {activeCount}
            </span>
          )}
        </Button>
        <Drawer
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          side="right"
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
            <h3 className="font-semibold text-gray-100">Filters</h3>
            <button
              onClick={() => setDrawerOpen(false)}
              className="h-8 w-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-200 hover:bg-gray-800"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          {filterFields}
        </Drawer>
      </>
    );
  }

  return <div className={className}>{filterFields}</div>;
};
