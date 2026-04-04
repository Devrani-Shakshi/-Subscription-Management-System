/* ── Billing domain types ─────────────────────────── */

export type InvoiceStatus = 'draft' | 'confirmed' | 'paid' | 'overdue' | 'cancelled' | 'partial';
export type PaymentMethod = 'credit_card' | 'bank_transfer' | 'cash' | 'check' | 'other';
export type DunningStatus = 'pending' | 'success' | 'failed' | 'skipped';

/* ── Invoice ──────────────────────────────────────── */

export interface InvoiceLineItem {
  id: string;
  product: string;
  description: string;
  quantity: number;
  unitPrice: number;
  taxPercent: number;
  discount: number;
  amount: number;
}

export interface Invoice {
  id: string;
  number: string;
  customerId: string;
  customerName: string;
  customerEmail: string;
  customerAddress: string;
  subscriptionId: string;
  subscriptionName: string;
  status: InvoiceStatus;
  invoiceDate: string;
  dueDate: string;
  lineItems: InvoiceLineItem[];
  subtotal: number;
  discountTotal: number;
  taxTotal: number;
  total: number;
  amountPaid: number;
  amountDue: number;
  notes: string;
  paymentTerms: string;
  createdAt: string;
  updatedAt: string;
}

export interface InvoiceFilters {
  status?: string;
  customer?: string;
  dateFrom?: string;
  dateTo?: string;
  amountMin?: string;
  amountMax?: string;
  page?: number;
  limit?: number;
}

export interface GenerateInvoicePayload {
  subscriptionId: string;
  invoiceDate: string;
  dueDate: string;
}

/* ── Payment ──────────────────────────────────────── */

export interface Payment {
  id: string;
  invoiceId: string;
  invoiceNumber: string;
  customerId: string;
  customerName: string;
  amount: number;
  method: PaymentMethod;
  date: string;
  notes: string;
  createdAt: string;
}

export interface PaymentFilters {
  method?: string;
  customer?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  limit?: number;
}

export interface RecordPaymentPayload {
  invoiceId: string;
  amount: number;
  method: PaymentMethod;
  date: string;
  notes: string;
}

export interface PaymentSummary {
  totalReceived: number;
  outstanding: number;
  overdue: number;
}

/* ── Dunning ──────────────────────────────────────── */

export interface DunningSchedule {
  id: string;
  invoiceId: string;
  invoiceNumber: string;
  customerId: string;
  customerName: string;
  attempt: number;
  scheduledDate: string;
  status: DunningStatus;
  result: string;
  resultJson: Record<string, unknown>;
  nextRetryDate: string | null;
  createdAt: string;
}

export interface DunningFilters {
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  limit?: number;
}

export interface DunningSummary {
  activeSequences: number;
  retriesToday: number;
  suspendedThisMonth: number;
}

/* ── Revenue ──────────────────────────────────────── */

export interface RevenueTimelinePoint {
  month: string;
  recognized: number;
  deferred: number;
  cumulative: number;
  newInvoices: number;
}

export interface RevenueSummary {
  recognizedThisMonth: number;
  deferred: number;
  cumulativeYTD: number;
}

export interface RevenueData {
  summary: RevenueSummary;
  timeline: RevenueTimelinePoint[];
}

export interface RevenueFilters {
  dateFrom?: string;
  dateTo?: string;
}

/* ── Payment history for invoice detail ───────────── */

export interface InvoicePaymentRecord {
  id: string;
  amount: number;
  method: PaymentMethod;
  date: string;
}

export interface InvoiceAuditEntry {
  id: string;
  action: string;
  user: string;
  timestamp: string;
  details: string;
}

/* ── Subscription (for searchable select) ─────────── */

export interface SubscriptionOption {
  id: string;
  name: string;
  customerName: string;
  amount: number;
}

/* ── Unpaid invoice (for payment select) ──────────── */

export interface UnpaidInvoiceOption {
  id: string;
  number: string;
  customerName: string;
  total: number;
  amountDue: number;
  isOverdue: boolean;
}
