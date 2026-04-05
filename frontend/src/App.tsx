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
import { NotFoundPage } from '@/pages/auth/NotFoundPage';
import { ErrorBoundary } from '@/components/layout/ErrorBoundary';
import { DashboardPage as AdminDashboard } from '@/pages/admin/AdminDashboard';
import { CompaniesPage } from '@/pages/admin/CompaniesPage';
import { CompanyDetailPage } from '@/pages/admin/CompanyDetailPage';
import { AuditLogPage } from '@/pages/admin/AuditLogPage';
import { CompanyDashboard } from '@/pages/company/CompanyDashboard';
import { SubscriptionsPage } from '@/pages/company/SubscriptionsPage';
import { CreateSubscriptionWizard } from '@/pages/company/CreateSubscriptionWizard';
import { SubscriptionDetailPage } from '@/pages/company/SubscriptionDetailPage';
import { ProductsPage } from '@/pages/company/ProductsPage';
import { PlansPage } from '@/pages/company/PlansPage';
import { CustomersPage } from '@/pages/company/CustomersPage';
import { CustomerDetailPage } from '@/pages/company/CustomerDetailPage';
import { TemplatesPage } from '@/pages/company/TemplatesPage';
import { DiscountsPage } from '@/pages/company/DiscountsPage';
import { TaxesPage } from '@/pages/company/TaxesPage';
import { InvoicesPage } from '@/pages/company/InvoicesPage';
import { InvoiceDetailPage } from '@/pages/company/InvoiceDetailPage';
import { PaymentsPage } from '@/pages/company/PaymentsPage';
import { DunningPage } from '@/pages/company/DunningPage';
import { RevenuePage } from '@/pages/company/RevenuePage';
import { ChurnPage } from '@/pages/company/ChurnPage';
import { AuditPage } from '@/pages/company/AuditPage';
import { MySubscriptionPage } from '@/pages/portal/MySubscriptionPage';
import { PlansPage as PortalPlansPage } from '@/pages/portal/PlansPage';
import { InvoicesPage as PortalInvoicesPage } from '@/pages/portal/InvoicesPage';
import { PaymentsPage as PortalPaymentsPage } from '@/pages/portal/PaymentsPage';
import { ProfilePage } from '@/pages/portal/ProfilePage';

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
        <ErrorBoundary>
        <Routes>
          {/* Public auth routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/invite/:token" element={<InviteAcceptPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />

          {/* Public plans page */}
          <Route path="/plans" element={<PortalPlansPage />} />

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
              <Route path="/admin/settings" element={<ProfilePage />} />
            </Route>
          </Route>

          {/* Company */}
          <Route element={<PrivateRoute allowedRoles={['company']} />}>
            <Route element={<AppShell />}>
              <Route path="/company" element={<CompanyDashboard />} />
              <Route path="/company/dashboard" element={<CompanyDashboard />} />
              <Route path="/company/products" element={<ProductsPage />} />
              <Route path="/company/plans" element={<PlansPage />} />
              <Route path="/company/subscriptions" element={<SubscriptionsPage />} />
              <Route path="/company/subscriptions/new" element={<CreateSubscriptionWizard />} />
              <Route path="/company/subscriptions/:id" element={<SubscriptionDetailPage />} />
              <Route path="/company/customers" element={<CustomersPage />} />
              <Route path="/company/customers/:id" element={<CustomerDetailPage />} />
              <Route path="/company/invoices" element={<InvoicesPage />} />
              <Route path="/company/invoices/:id" element={<InvoiceDetailPage />} />
              <Route path="/company/payments" element={<PaymentsPage />} />
              <Route path="/company/discounts" element={<DiscountsPage />} />
              <Route path="/company/taxes" element={<TaxesPage />} />
              <Route path="/company/templates" element={<TemplatesPage />} />
              <Route path="/company/churn" element={<ChurnPage />} />
              <Route path="/company/dunning" element={<DunningPage />} />
              <Route path="/company/revenue" element={<RevenuePage />} />
              <Route path="/company/audit" element={<AuditPage />} />
              <Route path="/company/settings" element={<ProfilePage />} />
            </Route>
          </Route>

          {/* Portal user */}
          <Route element={<PrivateRoute allowedRoles={['portal_user']} />}>
            <Route element={<AppShell />}>
              <Route path="/portal" element={<Navigate to="/portal/my-subscription" replace />} />
              <Route path="/portal/my-subscription" element={<MySubscriptionPage />} />
              <Route path="/portal/plans" element={<PortalPlansPage />} />
              <Route path="/portal/invoices" element={<PortalInvoicesPage />} />
              <Route path="/portal/payments" element={<PortalPaymentsPage />} />
              <Route path="/portal/profile" element={<ProfilePage />} />
            </Route>
          </Route>

          {/* 404 catch-all */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
        </ErrorBoundary>

        <ToastConfig />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
