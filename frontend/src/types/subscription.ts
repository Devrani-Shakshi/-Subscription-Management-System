export type SubscriptionStatus =
  | 'draft'
  | 'quotation'
  | 'confirmed'
  | 'active'
  | 'paused'
  | 'closed'
  | 'cancelled';

export type PaymentTerms = 'net_7' | 'net_15' | 'net_30' | 'due_on_receipt';

export interface OrderLine {
  id: string;
  productId: string;
  productName: string;
  quantity: number;
  unitPrice: number;
  tax: number;
  amount: number;
}

export interface Subscription {
  id: string;
  number: string;
  customerId: string;
  customerName: string;
  customerEmail: string;
  planId: string;
  planName: string;
  status: SubscriptionStatus;
  startDate: string;
  expiryDate: string;
  mrr: number;
  paymentTerms: PaymentTerms;
  notes: string;
  pausable: boolean;
  renewable: boolean;
  orderLines: OrderLine[];
  createdAt: string;
  updatedAt: string;
}

export interface SubscriptionSummary {
  id: string;
  number: string;
  customerName: string;
  planName: string;
  status: SubscriptionStatus;
  startDate: string;
  expiryDate: string;
  mrr: number;
}

export interface SubscriptionFilters {
  page: number;
  limit: number;
  status?: string;
  planId?: string;
  search?: string;
  startFrom?: string;
  startTo?: string;
  expiryFrom?: string;
  expiryTo?: string;
  sortBy?: string;
  sortDir?: 'asc' | 'desc';
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  company: string;
  churnScore?: number;
}

export interface Plan {
  id: string;
  name: string;
  price: number;
  period: 'monthly' | 'quarterly' | 'annually';
  features: string[];
  isActive: boolean;
}

export interface Product {
  id: string;
  name: string;
  sku: string;
  unitPrice: number;
  category: string;
}

export interface WizardProduct {
  productId: string;
  productName: string;
  quantity: number;
  unitPrice: number;
}

export interface QuotationTemplate {
  id: string;
  name: string;
  planId: string;
  products: WizardProduct[];
}

export interface CreateSubscriptionPayload {
  customerId: string;
  planId: string;
  products: WizardProduct[];
  startDate: string;
  expiryDate: string;
  paymentTerms: PaymentTerms;
  notes: string;
}

export interface TransitionPayload {
  to: SubscriptionStatus;
}

export interface ProRataPreview {
  currentPlanName: string;
  newPlanName: string;
  todaysCharge: number;
  daysRemaining: number;
  effectiveDate: string;
}

export interface DowngradePreview {
  currentPlanName: string;
  newPlanName: string;
  downgradeAt: string;
  warnings: string[];
}

export interface InvoiceSummary {
  id: string;
  number: string;
  status: string;
  amount: number;
  dueDate: string;
  paidDate: string | null;
}

export interface AuditTimelineEntry {
  id: string;
  action: string;
  fromStatus: string;
  toStatus: string;
  actor: string;
  timestamp: string;
  details: string;
}

export interface ChurnRiskInfo {
  score: number;
  level: 'low' | 'medium' | 'high';
  signals: string[];
}

export interface DunningInfo {
  sequenceId: string;
  currentStep: number;
  totalSteps: number;
  nextAttempt: string;
  failedAttempts: number;
}

export interface BulkConflict {
  id: string;
  number: string;
  reason: string;
  skipped: boolean;
}

export interface BulkJobStatus {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total: number;
  succeeded: number;
  failed: number;
  progress: number;
  failures: Array<{ id: string; reason: string }>;
}

export type BulkAction = 'activate' | 'close' | 'apply_discount';

export interface WizardFormData {
  customerId: string;
  customerName: string;
  planId: string;
  planName: string;
  products: WizardProduct[];
  startDate: string;
  expiryDate: string;
  paymentTerms: PaymentTerms;
  notes: string;
}

export interface PlanOption {
  label: string;
  value: string;
}
