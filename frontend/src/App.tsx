import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { queryClient } from '@/lib/queryClient';
import { useAuthStore } from '@/stores/authStore';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { AppShell } from '@/components/layout/AppShell';
import { PrivateRoute } from '@/components/layout/PrivateRoute';
import { LoginPage } from '@/pages/auth/LoginPage';
import { RegisterPage } from '@/pages/auth/RegisterPage';
import { InviteAcceptPage } from '@/pages/auth/InviteAcceptPage';
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage';
import { ResetPasswordPage } from '@/pages/auth/ResetPasswordPage';
import { UnauthorizedPage } from '@/pages/auth/UnauthorizedPage';
import { DashboardPage as AdminDashboard } from '@/pages/admin/AdminDashboard';
import { CompaniesPage } from '@/pages/admin/CompaniesPage';
import { CompanyDetailPage } from '@/pages/admin/CompanyDetailPage';
import { AuditLogPage } from '@/pages/admin/AuditLogPage';
import { CompanyDashboard } from '@/pages/company/CompanyDashboard';
import { SubscriptionsPage } from '@/pages/company/SubscriptionsPage';
import { CreateSubscriptionWizard } from '@/pages/company/CreateSubscriptionWizard';
import { SubscriptionDetailPage } from '@/pages/company/SubscriptionDetailPage';
import { PortalDashboard } from '@/pages/portal/PortalDashboard';

const RoleRedirect: React.FC = () => {
  const user = useAuthStore((s) => s.user);

  if (!user) return <Navigate to="/login" replace />;

  const routeMap: Record<string, string> = {
    super_admin: '/admin',
    company: '/company',
    portal_user: '/portal',
  };

  return <Navigate to={routeMap[user.role] || '/login'} replace />;
};

const ToastConfig: React.FC = () => {
  const { isMobile } = useBreakpoint();

  return (
    <Toaster
      position={isMobile ? 'bottom-center' : 'top-right'}
      toastOptions={{
        duration: 4000,
        style: {
          background: '#1f2937',
          color: '#f3f4f6',
          border: '1px solid #374151',
          borderRadius: '12px',
          fontSize: '14px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
        },
        success: {
          iconTheme: {
            primary: '#34d399',
            secondary: '#1f2937',
          },
        },
        error: {
          iconTheme: {
            primary: '#f87171',
            secondary: '#1f2937',
          },
        },
      }}
    />
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public auth routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/invite/:token" element={<InviteAcceptPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />

          {/* Role redirect */}
          <Route path="/" element={<RoleRedirect />} />

          {/* Super Admin */}
          <Route element={<PrivateRoute allowedRoles={['super_admin']} />}>
            <Route element={<AppShell />}>
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/admin/dashboard" element={<AdminDashboard />} />
              <Route path="/admin/companies" element={<CompaniesPage />} />
              <Route path="/admin/companies/:tenantId" element={<CompanyDetailPage />} />
              <Route path="/admin/audit" element={<AuditLogPage />} />
              <Route path="/admin/settings" element={<AdminDashboard />} />
            </Route>
          </Route>

          {/* Company */}
          <Route element={<PrivateRoute allowedRoles={['company']} />}>
            <Route element={<AppShell />}>
              <Route path="/company" element={<CompanyDashboard />} />
              <Route path="/company/dashboard" element={<CompanyDashboard />} />
              <Route path="/company/products" element={<CompanyDashboard />} />
              <Route path="/company/plans" element={<CompanyDashboard />} />
              <Route path="/company/subscriptions" element={<SubscriptionsPage />} />
              <Route path="/company/subscriptions/new" element={<CreateSubscriptionWizard />} />
              <Route path="/company/subscriptions/:id" element={<SubscriptionDetailPage />} />
              <Route path="/company/customers" element={<CompanyDashboard />} />
              <Route path="/company/invoices" element={<CompanyDashboard />} />
              <Route path="/company/payments" element={<CompanyDashboard />} />
              <Route path="/company/discounts" element={<CompanyDashboard />} />
              <Route path="/company/taxes" element={<CompanyDashboard />} />
              <Route path="/company/templates" element={<CompanyDashboard />} />
              <Route path="/company/churn" element={<CompanyDashboard />} />
              <Route path="/company/dunning" element={<CompanyDashboard />} />
              <Route path="/company/revenue" element={<CompanyDashboard />} />
              <Route path="/company/audit" element={<CompanyDashboard />} />
            </Route>
          </Route>

          {/* Portal user */}
          <Route element={<PrivateRoute allowedRoles={['portal_user']} />}>
            <Route element={<AppShell />}>
              <Route path="/portal" element={<PortalDashboard />} />
              <Route path="/portal/my-subscription" element={<PortalDashboard />} />
              <Route path="/portal/invoices" element={<PortalDashboard />} />
              <Route path="/portal/payments" element={<PortalDashboard />} />
              <Route path="/portal/plans" element={<PortalDashboard />} />
              <Route path="/portal/profile" element={<PortalDashboard />} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        <ToastConfig />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
