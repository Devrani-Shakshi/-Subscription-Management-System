import React, { useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';

type DrawerSide = 'left' | 'right';

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  side?: DrawerSide;
  children: React.ReactNode;
  className?: string;
}

const SIDE_CLASSES: Record<DrawerSide, { panel: string; enter: string; exit: string }> = {
  left: {
    panel: 'left-0 top-0 bottom-0',
    enter: 'translate-x-0',
    exit: '-translate-x-full',
  },
  right: {
    panel: 'right-0 top-0 bottom-0',
    enter: 'translate-x-0',
    exit: 'translate-x-full',
  },
};

export const Drawer: React.FC<DrawerProps> = ({
  open,
  onClose,
  side = 'left',
  children,
  className = '',
}) => {
  const sideConfig = SIDE_CLASSES[side];

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (open) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [open, handleKeyDown]);

  if (!open) return null;

  const drawer = (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className={`
          absolute ${sideConfig.panel} w-[280px] max-w-[85vw]
          bg-gray-900 border-r border-gray-800 shadow-2xl
          transform transition-transform duration-300 ease-out
          ${sideConfig.enter}
          ${className}
        `.trim()}
        role="dialog"
        aria-modal="true"
      >
        {children}
      </div>
    </div>
  );

  return createPortal(drawer, document.body);
};
