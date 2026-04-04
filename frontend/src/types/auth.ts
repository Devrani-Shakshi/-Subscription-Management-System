import type { User } from './index';

export interface TenantBranding {
  name: string;
  logoUrl: string | null;
  primaryColor: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  data: {
    user: User;
    accessToken: string;
  };
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  tenantSlug: string;
}

export interface InviteDetails {
  email: string;
  invitedBy: string;
  role: string;
  companyName: string;
}

export interface InviteAcceptRequest {
  token: string;
  name: string;
  password: string;
}

export interface ResetRequestPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  password: string;
}

export interface TenantBrandingResponse {
  data: TenantBranding;
}

export interface InviteValidateResponse {
  data: InviteDetails;
}

export type AuthPageState = 'idle' | 'loading' | 'error' | 'success';

export interface AuthErrorResponse {
  message: string;
  retry_after?: number;
}
