import React from 'react';
import { NavLink } from 'react-router-dom';
import * as LucideIcons from 'lucide-react';

interface BottomNavItem {
  label: string;
  path: string;
  icon: string;
}

const PORTAL_NAV: BottomNavItem[] = [
  { label: 'Home', path: '/portal', icon: 'Home' },
  { label: 'Invoices', path: '/portal/invoices', icon: 'FileText' },
  { label: 'Payments', path: '/portal/payments', icon: 'CreditCard' },
  { label: 'Plans', path: '/portal/plans', icon: 'Layers' },
  { label: 'Profile', path: '/portal/profile', icon: 'UserCircle' },
];

function getIcon(name: string): React.FC<{ className?: string }> | null {
  const icons = LucideIcons as unknown as Record<string, React.FC<{ className?: string }>>;
  return icons[name] || null;
}

export const BottomNav: React.FC = () => {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-gray-900/95 backdrop-blur-xl border-t border-gray-800 lg:hidden safe-bottom">
      <div className="flex items-center justify-around h-16">
        {PORTAL_NAV.map((item) => {
          const Icon = getIcon(item.icon);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/portal'}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-0.5 min-w-[3rem] min-h-[2.75rem] px-2 py-1
                 transition-colors duration-200
                 ${isActive ? 'text-amber-400' : 'text-gray-500 hover:text-gray-300'}`
              }
            >
              {Icon && <Icon className="h-5 w-5" />}
              <span className="text-[10px] font-medium">{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};
