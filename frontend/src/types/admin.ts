export interface AdminDashboardData {
  totalCompanies: number;
  totalActiveSubs: number;
  platformMRR: number;
  platformChurnRate: number;
  newCompaniesThisMonth: number;
  alerts: AdminAlert[];
  topCompanies: AdminCompanySummary[];
}

export type AlertType = 'trial_expiring' | 'suspended' | 'dunning';
export type AlertSeverity = 'low' | 'medium' | 'high';

export interface AdminAlert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  companyName: string;
  companyId: string;
  message: string;
  createdAt: string;
}

export interface AdminCompanySummary {
  id: string;
  name: string;
  slug: string;
  status: string;
  mrr: number;
  activeSubs: number;
  trialEnds: string | null;
  createdAt: string;
  ownerEmail: string;
  hasActiveSubscriptions: boolean;
}

export interface AdminCompanyDetail extends AdminCompanySummary {
  totalCustomers: number;
  totalInvoices: number;
}

export interface AdminSubscription {
  id: string;
  customerName: string;
  planName: string;
  status: string;
  mrr: number;
  startDate: string;
  endDate: string | null;
}

export interface AdminCustomer {
  id: string;
  name: string;
  email: string;
  subscriptionStatus: string;
  planName: string;
  churnScore: number;
}

export interface AdminInvoice {
  id: string;
  number: string;
  status: string;
  total: number;
  dueDate: string;
}

export interface AuditEntry {
  id: string;
  actor: string;
  actorRole: string;
  companyName: string;
  companyId: string;
  entityType: string;
  entityId: string;
  action: string;
  timestamp: string;
  diff: AuditDiff | null;
}

export interface AuditDiff {
  before: Record<string, unknown>;
  after: Record<string, unknown>;
}

export interface CreateCompanyPayload {
  companyName: string;
  slug: string;
  ownerEmail: string;
}

export interface SlugCheckResponse {
  available: boolean;
  suggested?: string;
}

export interface AdminCompanyFilters {
  status: string;
  search: string;
  page: number;
  limit: number;
}

export interface AuditFilters {
  companyId: string;
  entityType: string;
  action: string;
  actor: string;
  dateFrom: string;
  dateTo: string;
  page: number;
  limit: number;
}
