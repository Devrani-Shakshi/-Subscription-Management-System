import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LogOut, ChevronLeft } from 'lucide-react';
import * as LucideIcons from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { ConfirmModal } from '@/components/ui';
import type { NavItem, Role } from '@/types';

interface SidebarProps {
  role: Role;
  navItems: NavItem[];
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

interface AccentConfig {
  logoBg: string;
  logoBorder: string;
  logoText: string;
  gradient: string;
  activeBg: string;
  activeText: string;
  activeBorder: string;
  activeIcon: string;
  badgeBg: string;
  badgeText: string;
  avatarBg: string;
  avatarBorder: string;
  avatarText: string;
}

const ACCENT_MAP: Record<Role, AccentConfig> = {
  super_admin: {
    logoBg: 'bg-violet-500/20',
    logoBorder: 'border-violet-500/30',
    logoText: 'text-violet-400',
    gradient: 'from-violet-600/20 to-violet-800/10',
    activeBg: 'bg-violet-500/10',
    activeText: 'text-violet-400',
    activeBorder: 'border-violet-500/20',
    activeIcon: 'text-violet-400',
    badgeBg: 'bg-violet-500/20',
    badgeText: 'text-violet-300',
    avatarBg: 'bg-violet-500/20',
    avatarBorder: 'border-violet-500/30',
    avatarText: 'text-violet-400',
  },
  company: {
    logoBg: 'bg-teal-500/20',
    logoBorder: 'border-teal-500/30',
    logoText: 'text-teal-400',
    gradient: 'from-teal-600/20 to-teal-800/10',
    activeBg: 'bg-teal-500/10',
    activeText: 'text-teal-400',
    activeBorder: 'border-teal-500/20',
    activeIcon: 'text-teal-400',
    badgeBg: 'bg-teal-500/20',
    badgeText: 'text-teal-300',
    avatarBg: 'bg-teal-500/20',
    avatarBorder: 'border-teal-500/30',
    avatarText: 'text-teal-400',
  },
  portal_user: {
    logoBg: 'bg-amber-500/20',
    logoBorder: 'border-amber-500/30',
    logoText: 'text-amber-400',
    gradient: 'from-amber-600/20 to-amber-800/10',
    activeBg: 'bg-amber-500/10',
    activeText: 'text-amber-400',
    activeBorder: 'border-amber-500/20',
    activeIcon: 'text-amber-400',
    badgeBg: 'bg-amber-500/20',
    badgeText: 'text-amber-300',
    avatarBg: 'bg-amber-500/20',
    avatarBorder: 'border-amber-500/30',
    avatarText: 'text-amber-400',
  },
};

const BASE_PATHS: Record<Role, string> = {
  super_admin: '/admin',
  company: '/company',
  portal_user: '/portal',
};

function getIcon(name: string): React.FC<{ className?: string }> | null {
  const icons = LucideIcons as unknown as Record<string, React.FC<{ className?: string }>>;
  return icons[name] || null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  role,
  navItems,
  collapsed = false,
  onToggleCollapse,
}) => {
  const { isTablet } = useBreakpoint();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const isCollapsed = collapsed || isTablet;
  const a = ACCENT_MAP[role];
  const basePath = BASE_PATHS[role];

  return (
    <>
      <aside
        className={`
          flex flex-col h-full bg-gray-900 border-r border-gray-800
          transition-all duration-300 ease-in-out
          ${isCollapsed ? 'w-[60px]' : 'w-[220px]'}
        `.trim()}
      >
        {/* Logo */}
        <div className={`flex items-center h-16 px-4 border-b border-gray-800 bg-gradient-to-r ${a.gradient}`}>
          <div className={`h-8 w-8 rounded-lg ${a.logoBg} border ${a.logoBorder} flex items-center justify-center shrink-0`}>
            <span className={`text-sm font-bold ${a.logoText}`}>S</span>
          </div>
          {!isCollapsed && (
            <span className="ml-3 text-sm font-bold text-gray-100 tracking-wider">
              SubFlow
            </span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {navItems.map((item) => {
            const Icon = getIcon(item.icon);
            const isActive =
              location.pathname === item.path ||
              (item.path !== basePath && location.pathname.startsWith(item.path));

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`
                  group flex items-center gap-3 px-3 py-2.5 rounded-lg
                  text-sm font-medium transition-all duration-200
                  min-h-[2.75rem]
                  ${isCollapsed ? 'justify-center' : ''}
                  ${
                    isActive
                      ? `${a.activeBg} ${a.activeText} border ${a.activeBorder}`
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60 border border-transparent'
                  }
                `.trim()}
                title={isCollapsed ? item.label : undefined}
              >
                {Icon && (
                  <Icon
                    className={`h-5 w-5 shrink-0 transition-colors ${
                      isActive ? a.activeIcon : 'text-gray-500 group-hover:text-gray-300'
                    }`}
                  />
                )}
                {!isCollapsed && (
                  <span className="truncate">{item.label}</span>
                )}
                {!isCollapsed && item.badge !== undefined && item.badge > 0 && (
                  <span className={`ml-auto h-5 min-w-[1.25rem] flex items-center justify-center rounded-full text-xs font-medium px-1.5 ${a.badgeBg} ${a.badgeText}`}>
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Collapse toggle */}
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className="hidden lg:flex items-center justify-center h-8 mx-2 mb-2 rounded-lg
                       text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronLeft
              className={`h-4 w-4 transition-transform duration-300 ${
                isCollapsed ? 'rotate-180' : ''
              }`}
            />
          </button>
        )}

        {/* User footer */}
        <div className="border-t border-gray-800 p-3">
          <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'}`}>
            <div className={`h-8 w-8 rounded-full ${a.avatarBg} border ${a.avatarBorder} flex items-center justify-center shrink-0`}>
              <span className={`text-xs font-bold ${a.avatarText}`}>
                {user?.name?.charAt(0)?.toUpperCase() || '?'}
              </span>
            </div>
            {!isCollapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200 truncate">
                  {user?.name || 'User'}
                </p>
                <p className="text-xs text-gray-500 truncate capitalize">
                  {role.replace('_', ' ')}
                </p>
              </div>
            )}
            <button
              onClick={() => setShowLogoutConfirm(true)}
              className={`h-8 w-8 flex items-center justify-center rounded-lg
                         text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors
                         ${isCollapsed ? 'mt-2' : ''}`}
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Logout Confirmation Modal */}
      <ConfirmModal
        open={showLogoutConfirm}
        onClose={() => setShowLogoutConfirm(false)}
        onConfirm={() => {
          setShowLogoutConfirm(false);
          logout();
        }}
        title="Confirm Logout"
        message="Are you sure you want to log out? You will need to sign in again to access your account."
        confirmLabel="Logout"
        variant="danger"
      />
    </>
  );
};
