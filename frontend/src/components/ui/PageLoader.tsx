import React from 'react';

interface PageLoaderProps {
  className?: string;
}

export const PageLoader: React.FC<PageLoaderProps> = ({
  className = '',
}) => {
  return (
    <div className={`space-y-6 p-6 animate-pulse ${className}`}>
      {/* Header skeleton */}
      <div className="space-y-3">
        <div className="h-4 w-32 bg-gray-800 rounded" />
        <div className="h-8 w-64 bg-gray-800 rounded" />
        <div className="h-4 w-48 bg-gray-800 rounded" />
      </div>

      {/* Stat cards skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-24 bg-gray-900 border border-gray-800 rounded-xl p-4"
          >
            <div className="h-3 w-20 bg-gray-800 rounded mb-3" />
            <div className="h-6 w-16 bg-gray-800 rounded mb-2" />
            <div className="h-3 w-12 bg-gray-800 rounded" />
          </div>
        ))}
      </div>

      {/* Table skeleton */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="h-10 bg-gray-800/50 border-b border-gray-800" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="flex items-center gap-4 px-4 py-3 border-b border-gray-800/30"
          >
            <div className="h-4 w-1/4 bg-gray-800 rounded" />
            <div className="h-4 w-1/3 bg-gray-800 rounded" />
            <div className="h-4 w-1/6 bg-gray-800 rounded" />
            <div className="h-4 w-1/6 bg-gray-800 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
};
