import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, Bell, LogOut, User, ChevronRight } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useUiStore } from '@/stores/uiStore';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import type { Role } from '@/types';

interface TopbarProps {
  breadcrumbs?: { label: string; href?: string }[];
}

interface AvatarStyle {
  bg: string;
  border: string;
  text: string;
  ring: string;
}

const AVATAR_STYLES: Record<Role, AvatarStyle> = {
  super_admin: {
    bg: 'bg-violet-500/20',
    border: 'border-violet-500/30',
    text: 'text-violet-400',
    ring: 'hover:ring-violet-500/40',
  },
  company: {
    bg: 'bg-teal-500/20',
    border: 'border-teal-500/30',
    text: 'text-teal-400',
    ring: 'hover:ring-teal-500/40',
  },
  portal_user: {
    bg: 'bg-amber-500/20',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    ring: 'hover:ring-amber-500/40',
  },
};

export const Topbar: React.FC<TopbarProps> = ({ breadcrumbs }) => {
  const { isMobile } = useBreakpoint();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const avatarStyle = AVATAR_STYLES[user?.role ?? 'super_admin'];

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-30 h-16 bg-gray-950/80 backdrop-blur-xl border-b border-gray-800">
      <div className="flex items-center justify-between h-full px-4 lg:px-6">
        {/* Left */}
        <div className="flex items-center gap-4">
          {isMobile && (
            <button
              onClick={toggleSidebar}
              className="h-10 w-10 flex items-center justify-center rounded-lg
                         text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors"
              aria-label="Toggle menu"
            >
              <Menu className="h-5 w-5" />
            </button>
          )}

          {isMobile ? (
            <span className="text-sm font-bold text-gray-100 tracking-wider">
              SubFlow
            </span>
          ) : (
            breadcrumbs &&
            breadcrumbs.length > 0 && (
              <nav className="flex items-center gap-1 text-sm">
                {breadcrumbs.map((crumb, i) => (
                  <React.Fragment key={i}>
                    {i > 0 && (
                      <ChevronRight className="h-3.5 w-3.5 text-gray-600" />
                    )}
                    {crumb.href ? (
                      <button
                        onClick={() => navigate(crumb.href!)}
                        className="text-gray-400 hover:text-gray-200 transition-colors"
                      >
                        {crumb.label}
                      </button>
                    ) : (
                      <span className="text-gray-300 font-medium">
                        {crumb.label}
                      </span>
                    )}
                  </React.Fragment>
                ))}
              </nav>
            )
          )}
        </div>

        {/* Right */}
        <div className="flex items-center gap-2">
          {user?.role !== 'portal_user' && (
            <button
              className="relative h-10 w-10 flex items-center justify-center rounded-lg
                         text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors"
              aria-label="Notifications"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 ring-2 ring-gray-950" />
            </button>
          )}

          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className={`h-9 w-9 rounded-full ${avatarStyle.bg} border ${avatarStyle.border}
                         flex items-center justify-center transition-all duration-200
                         hover:ring-2 ${avatarStyle.ring}`}
            >
              <span className={`text-xs font-bold ${avatarStyle.text}`}>
                {user?.name?.charAt(0)?.toUpperCase() || '?'}
              </span>
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-gray-900 border border-gray-800 rounded-xl shadow-2xl shadow-black/40 animate-scale-in overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-800">
                  <p className="text-sm font-medium text-gray-100">
                    {user?.name || 'User'}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {user?.email || ''}
                  </p>
                </div>
                <div className="py-1">
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      navigate(
                        user?.role === 'portal_user'
                          ? '/portal/profile'
                          : user?.role === 'super_admin'
                          ? '/admin/settings'
                          : '/company/settings'
                      );
                    }}
                    className="flex items-center gap-3 w-full px-4 py-2.5 text-sm
                               text-gray-300 hover:text-gray-100 hover:bg-gray-800 transition-colors"
                  >
                    <User className="h-4 w-4" />
                    Profile
                  </button>
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      logout();
                      navigate('/login');
                    }}
                    className="flex items-center gap-3 w-full px-4 py-2.5 text-sm
                               text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
