import React, { useRef, useEffect } from 'react';
import type { TabItem } from '@/types';

interface TabsProps {
  tabs: TabItem[];
  active: string;
  onChange: (key: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  active,
  onChange,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      const activeTab = containerRef.current.querySelector(
        `[data-tab="${active}"]`
      );
      if (activeTab) {
        activeTab.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
          inline: 'center',
        });
      }
    }
  }, [active]);

  return (
    <div
      ref={containerRef}
      className={`flex overflow-x-auto scrollbar-hide border-b border-gray-800 ${className}`}
    >
      {tabs.map((tab) => {
        const isActive = tab.key === active;

        return (
          <button
            key={tab.key}
            data-tab={tab.key}
            onClick={() => onChange(tab.key)}
            className={`
              relative flex items-center gap-2 px-4 py-3 text-sm font-medium
              whitespace-nowrap transition-colors duration-200
              border-b-2 -mb-px min-h-[2.75rem]
              ${
                isActive
                  ? 'text-violet-400 border-violet-500'
                  : 'text-gray-400 border-transparent hover:text-gray-200 hover:border-gray-700'
              }
            `.trim()}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span
                className={`h-5 min-w-[1.25rem] flex items-center justify-center
                  rounded-full text-xs px-1.5 font-medium
                  ${
                    isActive
                      ? 'bg-violet-500/20 text-violet-300'
                      : 'bg-gray-800 text-gray-500'
                  }
                `}
              >
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
