// ── Product ─────────────────────────────────────────────────
export interface ProductVariant {
  id?: string;
  attribute: string;
  value: string;
  extra_price: number;
}

export interface Product {
  id: string;
  name: string;
  type: 'physical' | 'digital' | 'service';
  sales_price: number;
  cost_price: number;
  variants: ProductVariant[];
  created_at: string;
}

export interface ProductFormData {
  name: string;
  type: 'physical' | 'digital' | 'service';
  sales_price: number;
  cost_price: number;
  variants: ProductVariant[];
}

// ── Plan ────────────────────────────────────────────────────
export type BillingPeriod =
  | 'daily'
  | 'weekly'
  | 'monthly'
  | 'quarterly'
  | 'yearly';

export interface PlanFeature {
  key: string;
  value: string;
}

export interface Plan {
  id: string;
  name: string;
  price: number;
  billing_period: BillingPeriod;
  min_quantity: number;
  start_date: string;
  end_date: string | null;
  auto_close: boolean;
  closable: boolean;
  pausable: boolean;
  renewable: boolean;
  features_json: PlanFeature[];
  subscriptions_count: number;
  created_at: string;
}

export interface PlanFormData {
  name: string;
  price: number;
  billing_period: BillingPeriod;
  min_quantity: number;
  start_date: string;
  end_date?: string;
  auto_close: boolean;
  closable: boolean;
  pausable: boolean;
  renewable: boolean;
  features_json: PlanFeature[];
}

// ── Customer ────────────────────────────────────────────────
export type ChurnLevel = 'high' | 'medium' | 'low';

export interface Customer {
  id: string;
  name: string;
  email: string;
  plan_name: string | null;
  subscription_status: string | null;
  churn_score: number;
  last_invoice_date: string | null;
  created_at: string;
}

export interface CustomerDetail {
  id: string;
  name: string;
  email: string;
  subscription: CustomerSubscription | null;
  churn: CustomerChurn | null;
  recent_invoices: CustomerInvoice[];
  invoices: CustomerInvoice[];
  dunning_history: DunningEntry[];
}

export interface CustomerSubscription {
  id: string;
  plan_name: string;
  status: string;
  start_date: string;
  expiry_date: string | null;
  mrr: number;
}

export interface CustomerChurn {
  score: number;
  signals: ChurnSignal[];
}

export interface ChurnSignal {
  label: string;
  impact: 'positive' | 'negative' | 'neutral';
  value: string;
}

export interface CustomerInvoice {
  id: string;
  invoice_number: string;
  status: string;
  total: number;
  due_date: string;
  paid_at: string | null;
  created_at: string;
}

export interface DunningEntry {
  id: string;
  type: string;
  sent_at: string;
  status: string;
  message: string;
}

export interface InviteCustomerData {
  email: string;
}

// ── Template ────────────────────────────────────────────────
export interface TemplateProductLine {
  product_id: string;
  product_name?: string;
  quantity: number;
}

export interface Template {
  id: string;
  name: string;
  plan_id: string;
  plan_name: string;
  validity_days: number;
  product_lines: TemplateProductLine[];
  created_at: string;
}

export interface TemplateFormData {
  name: string;
  validity_days: number;
  plan_id: string;
  product_lines: TemplateProductLine[];
}

// ── Discount ────────────────────────────────────────────────
export type DiscountType = 'fixed' | 'percent';
export type DiscountAppliesTo = 'product' | 'subscription';

export interface Discount {
  id: string;
  name: string;
  type: DiscountType;
  value: number;
  min_purchase: number;
  min_quantity: number;
  start_date: string;
  end_date: string | null;
  usage_limit: number | null;
  used_count: number;
  applies_to: DiscountAppliesTo;
  created_at: string;
}

export interface DiscountFormData {
  name: string;
  type: DiscountType;
  value: number;
  min_purchase: number;
  min_quantity: number;
  start_date: string;
  end_date?: string;
  usage_limit?: number | null;
  applies_to: DiscountAppliesTo;
}

// ── Tax ─────────────────────────────────────────────────────
export interface Tax {
  id: string;
  name: string;
  rate: number;
  type: string;
  created_at: string;
}

export interface TaxFormData {
  name: string;
  rate: number;
  type: string;
}

// ── Dashboard ───────────────────────────────────────────────
export interface MetricItem {
  name: string;
  value: string;
  raw_value: string;
  trend: 'up' | 'down' | 'flat';
  delta: string;
  period: string;
}

export interface DashboardMetrics {
  metrics: Record<string, MetricItem>;
}

export interface MonthlySubData {
  month: string;
  count: number;
}

export interface MrrDataPoint {
  month: string;
  mrr: number;
}

export interface AtRiskCustomer {
  id: string;
  name: string;
  email: string;
  score: number;
  risk_level: 'high' | 'medium' | 'low';
}

export interface ActiveDunning {
  id: string;
  invoice_number: string;
  customer_name: string;
  attempt: number;
  next_retry: string;
  status: string;
}

export interface RecentActivity {
  id: string;
  entity_type: string;
  action: string;
  entity_id: string;
  description: string;
  created_at: string;
}

export interface DashboardData {
  metrics: Record<string, MetricItem>;
  subscriptions_chart: MonthlySubData[];
  mrr_chart: MrrDataPoint[];
  at_risk_customers: AtRiskCustomer[];
  active_dunning: ActiveDunning[];
  recent_activity: RecentActivity[];
}

// ── Churn Page ──────────────────────────────────────────────
export interface ChurnSignalDetail {
  key: string;
  weight: number;
  triggered: boolean;
  detail: string;
}

export interface ChurnScoreEntry {
  id: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  plan_name?: string;
  score: number;
  risk_level: 'high' | 'medium' | 'low';
  signals: ChurnSignalDetail[];
  last_active?: string;
  computed_at: string;
}

export interface ChurnFilters {
  risk_level?: string;
  plan_id?: string;
  page: number;
  limit: number;
  min_score?: number;
}

export interface ChurnStats {
  high: number;
  medium: number;
  low: number;
}

// ── Audit Page ──────────────────────────────────────────────
export type AuditAction = 'create' | 'update' | 'delete' | 'status_change';

export interface AuditLogEntry {
  id: string;
  actor_id: string;
  actor_name: string | null;
  actor_role: string;
  entity_type: string;
  entity_id: string;
  action: AuditAction;
  diff_json: Record<string, DiffField>;
  created_at: string;
}

export interface DiffField {
  old: string | number | boolean | null;
  new: string | number | boolean | null;
}

export interface AuditFilters {
  entity_type?: string;
  action?: string;
  date_from?: string;
  date_to?: string;
  page: number;
  page_size: number;
}
