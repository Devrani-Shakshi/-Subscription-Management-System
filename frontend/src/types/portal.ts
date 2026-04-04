/* ── Portal domain types ─────────────────────────── */

export type PortalInvoiceStatus = 'paid' | 'overdue' | 'pending' | 'cancelled';
export type PortalPaymentStatus = 'success' | 'failed' | 'pending' | 'refunded';

/* ── Tenant Branding ─────────────────────────────── */

export interface TenantBranding {
  companyName: string;
  logo: string | null;
  primaryColor: string;
  slug: string;
}

/* ── Portal Subscription ─────────────────────────── */

export interface PortalOrderLine {
  id: string;
  product: string;
  quantity: number;
  unitPrice: number;
  total: number;
}

export interface PortalSubscription {
  id: string;
  planId: string;
  planName: string;
  billingPeriod: string;
  status: string;
  price: number;
  nextBillingDate: string;
  startDate: string;
  expiryDate: string | null;
  orderLines: PortalOrderLine[];
  subtotal: number;
  tax: number;
  discount: number;
  grandTotal: number;
  recentInvoices: PortalInvoice[];
  scheduledDowngrade: ScheduledDowngrade | null;
}

export interface ScheduledDowngrade {
  planName: string;
  effectiveDate: string;
}

/* ── Portal Plan ─────────────────────────────────── */

export interface PortalPlan {
  id: string;
  name: string;
  price: number;
  billingPeriod: string;
  features: string[];
  popular: boolean;
}

/* ── Portal Invoice ──────────────────────────────── */

export interface PortalInvoice {
  id: string;
  number: string;
  date: string;
  dueDate: string;
  amount: number;
  status: PortalInvoiceStatus;
}

export interface PortalInvoiceFilters {
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  limit?: number;
}

/* ── Portal Payment ──────────────────────────────── */

export interface PortalPayment {
  id: string;
  date: string;
  invoiceNumber: string;
  amount: number;
  method: string;
  status: PortalPaymentStatus;
}

/* ── Pro-Rata and Downgrade Preview ──────────────── */

export interface PortalProRataPreview {
  todaysCharge: number;
  daysRemaining: number;
  newPlanName: string;
  effectiveDate: string;
}

export interface PortalDowngradePreview {
  newPlanName: string;
  effectiveDate: string;
  warnings: string[];
}

/* ── Payment Form ────────────────────────────────── */

export interface PortalPaymentPayload {
  invoiceId: string;
  cardNumber: string;
  expiry: string;
  cvv: string;
  cardholderName: string;
}

export type PaymentState = 'idle' | 'processing' | 'success' | 'error';

/* ── Profile ─────────────────────────────────────── */

export interface PortalProfile {
  name: string;
  email: string;
  street: string;
  city: string;
  state: string;
  country: string;
  zip: string;
}

export interface ChangePasswordPayload {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

/* ── Sessions ────────────────────────────────────── */

export interface ActiveSession {
  id: string;
  device: string;
  ip: string;
  lastActive: string;
  isCurrent: boolean;
}

/* ── Cancel Subscription ─────────────────────────── */

export type CancelStep = 'consequences' | 'reason';

export interface CancelSubscriptionPayload {
  reason?: string;
}
