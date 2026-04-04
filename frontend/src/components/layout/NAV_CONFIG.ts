import type { NavItem, Role } from '@/types';

export const NAV_CONFIG: Record<Role, NavItem[]> = {
  super_admin: [
    { label: 'Dashboard', path: '/admin', icon: 'LayoutDashboard' },
    { label: 'Companies', path: '/admin/companies', icon: 'Building2' },
    { label: 'Audit Log', path: '/admin/audit', icon: 'ScrollText' },
    { label: 'Settings', path: '/admin/settings', icon: 'Settings' },
  ],
  company: [
    { label: 'Dashboard', path: '/company', icon: 'LayoutDashboard' },
    { label: 'Products', path: '/company/products', icon: 'Package' },
    { label: 'Plans', path: '/company/plans', icon: 'Layers' },
    { label: 'Subscriptions', path: '/company/subscriptions', icon: 'RefreshCw' },
    { label: 'Customers', path: '/company/customers', icon: 'Users' },
    { label: 'Invoices', path: '/company/invoices', icon: 'FileText' },
    { label: 'Payments', path: '/company/payments', icon: 'CreditCard' },
    { label: 'Discounts', path: '/company/discounts', icon: 'PercentDiamond' },
    { label: 'Taxes', path: '/company/taxes', icon: 'Receipt' },
    { label: 'Templates', path: '/company/templates', icon: 'FileCode' },
    { label: 'Churn', path: '/company/churn', icon: 'UserMinus' },
    { label: 'Dunning', path: '/company/dunning', icon: 'AlertCircle' },
    { label: 'Revenue', path: '/company/revenue', icon: 'TrendingUp' },
    { label: 'Audit', path: '/company/audit', icon: 'ScrollText' },
  ],
  portal_user: [
    { label: 'My Subscription', path: '/portal', icon: 'RefreshCw' },
    { label: 'Invoices', path: '/portal/invoices', icon: 'FileText' },
    { label: 'Payments', path: '/portal/payments', icon: 'CreditCard' },
    { label: 'Plans', path: '/portal/plans', icon: 'Layers' },
    { label: 'Profile', path: '/portal/profile', icon: 'UserCircle' },
  ],
};
