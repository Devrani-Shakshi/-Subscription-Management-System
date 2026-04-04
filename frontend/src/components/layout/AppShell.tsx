import React, { useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useUiStore } from '@/stores/uiStore';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { useIdleTimer } from '@/hooks/useIdleTimer';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { BottomNav } from './BottomNav';
import { Drawer } from '@/components/ui/Drawer';
import { NAV_CONFIG } from './NAV_CONFIG';

export const AppShell: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const location = useLocation();
  const { isMobile, isDesktop } = useBreakpoint();
  const sidebarOpen = useUiStore((s) => s.sidebarOpen);
  const setSidebarOpen = useUiStore((s) => s.setSidebarOpen);
  const setActiveRoute = useUiStore((s) => s.setActiveRoute);

  const role = user?.role ?? 'portal_user';
  const navItems = NAV_CONFIG[role];
  const { isWarning, remainingSeconds } = useIdleTimer(role);

  useEffect(() => {
    setActiveRoute(location.pathname);
  }, [location.pathname, setActiveRoute]);

  useEffect(() => {
    const handleIdleTimeout = () => {
      logout();
      navigate('/login');
    };
    window.addEventListener('idle-timeout', handleIdleTimeout);
    return () => window.removeEventListener('idle-timeout', handleIdleTimeout);
  }, [logout, navigate]);

  // Close mobile sidebar on route change
  useEffect(() => {
    if (isMobile) setSidebarOpen(false);
  }, [location.pathname, isMobile, setSidebarOpen]);

  const showBottomNav = isMobile && role === 'portal_user';

  return (
    <div className="flex h-dvh overflow-hidden bg-gray-950">
      {/* Desktop sidebar */}
      {!isMobile && (
        <Sidebar role={role} navItems={navItems} />
      )}

      {/* Mobile sidebar drawer */}
      {isMobile && (
        <Drawer
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          side="left"
        >
          <Sidebar role={role} navItems={navItems} />
        </Drawer>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Topbar />

        {/* Session warning banner */}
        {isWarning && (
          <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 flex items-center gap-2 animate-slide-down">
            <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
            <span className="text-sm text-amber-300">
              Session expiring in{' '}
              <span className="font-bold">{remainingSeconds}s</span>. Move your
              mouse to stay signed in.
            </span>
          </div>
        )}

        {/* Page content */}
        <main
          className={`
            flex-1 overflow-y-auto
            ${isDesktop ? 'p-6' : 'p-4'}
            ${showBottomNav ? 'pb-20' : ''}
          `.trim()}
        >
          <Outlet />
        </main>
      </div>

      {/* Portal bottom nav (mobile) */}
      {showBottomNav && <BottomNav />}
    </div>
  );
};
