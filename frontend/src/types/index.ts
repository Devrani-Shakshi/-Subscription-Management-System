export type Role = 'super_admin' | 'company' | 'portal_user';

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  tenantId: string | null;
}

export interface ApiResponse<T> {
  data: T;
  meta?: ApiMeta;
  errors?: ApiFieldError[];
}

export interface ApiMeta {
  total: number;
  page: number;
  limit: number;
}

export interface ApiFieldError {
  field: string;
  message: string;
}

export interface PaginationParams {
  page: number;
  limit: number;
}

export interface SortParams {
  sortBy: string;
  sortDir: 'asc' | 'desc';
}

export interface FilterParams {
  [key: string]: string | number | boolean | undefined;
}

export interface NavItem {
  label: string;
  path: string;
  icon: string;
  badge?: number;
}

export interface Crumb {
  label: string;
  href?: string;
}

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  width?: string;
  sortable?: boolean;
}

export interface FilterConfig {
  key: string;
  label: string;
  type: 'select' | 'date' | 'search';
  options?: { label: string; value: string }[];
}

export interface StatCardData {
  label: string;
  value: string | number;
  change?: { value: number; positive: boolean };
  icon?: string;
  color?: 'violet' | 'teal' | 'amber' | 'rose' | 'blue';
}

export interface TabItem {
  key: string;
  label: string;
  count?: number;
}

export type {
  SubscriptionStatus,
  PaymentTerms,
  OrderLine,
  Subscription,
  SubscriptionSummary,
  SubscriptionFilters,
  Customer,
  Plan,
  Product,
  WizardProduct,
  QuotationTemplate,
  CreateSubscriptionPayload,
  TransitionPayload,
  ProRataPreview,
  DowngradePreview,
  InvoiceSummary,
  AuditTimelineEntry,
  ChurnRiskInfo,
  DunningInfo,
  BulkConflict,
  BulkJobStatus,
  BulkAction,
  WizardFormData,
  PlanOption,
} from './subscription';
