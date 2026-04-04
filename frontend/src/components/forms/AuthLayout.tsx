import React from 'react';
import { Link } from 'react-router-dom';
import type { TenantBranding } from '@/types/auth';

interface AuthLayoutProps {
  branding?: TenantBranding | null;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

const PlatformLogo: React.FC = () => (
  <div className="flex items-center gap-3">
    <div className="h-12 w-12 rounded-2xl bg-violet-500/20 border border-violet-500/30 flex items-center justify-center glow-violet">
      <span className="text-lg font-bold text-violet-400">S</span>
    </div>
    <div>
      <h2 className="text-xl font-bold text-gray-50">SubFlow</h2>
      <p className="text-xs text-gray-500">Subscription Management</p>
    </div>
  </div>
);

interface BrandingPanelProps {
  branding?: TenantBranding | null;
}

const BrandingPanel: React.FC<BrandingPanelProps> = ({ branding }) => (
  <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gray-900 items-center justify-center">
    {/* Background decorations */}
    <div className="absolute inset-0">
      <div className="absolute top-1/4 -left-20 h-64 w-64 rounded-full bg-violet-500/10 blur-3xl" />
      <div className="absolute bottom-1/4 -right-20 h-64 w-64 rounded-full bg-violet-600/10 blur-3xl" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-violet-500/5 blur-3xl" />

      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(139,92,246,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.3) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />
    </div>

    <div className="relative z-10 text-center px-12 max-w-md">
      {branding?.logoUrl ? (
        <img
          src={branding.logoUrl}
          alt={branding.name}
          className="h-20 w-20 object-contain mx-auto mb-6 rounded-2xl"
        />
      ) : (
        <div className="h-20 w-20 rounded-2xl bg-violet-500/20 border border-violet-500/30 flex items-center justify-center mx-auto mb-6 glow-violet">
          <span className="text-3xl font-bold text-violet-400">S</span>
        </div>
      )}
      <h1 className="text-3xl font-bold text-gray-50 mb-3">
        {branding?.name || 'SubFlow'}
      </h1>
      <p className="text-gray-400 text-sm leading-relaxed">
        {branding
          ? `Welcome to ${branding.name}. Sign in to manage your subscriptions.`
          : 'The modern platform for subscription management. Track, bill, and grow.'}
      </p>

      {/* Feature pills */}
      <div className="mt-8 flex flex-wrap justify-center gap-2">
        {['Billing', 'Analytics', 'Automation', 'Portal'].map((feature) => (
          <span
            key={feature}
            className="px-3 py-1 text-xs font-medium text-violet-300 bg-violet-500/10 border border-violet-500/20 rounded-full"
          >
            {feature}
          </span>
        ))}
      </div>
    </div>
  </div>
);

export const AuthLayout: React.FC<AuthLayoutProps> = ({
  branding,
  title,
  subtitle,
  children,
  footer,
}) => {
  return (
    <div className="min-h-dvh flex bg-gray-950">
      {/* Left branding panel — desktop only */}
      <BrandingPanel branding={branding} />

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center px-4 py-8 sm:px-6 lg:px-12">
        <div className="w-full max-w-md animate-fade-in">
          {/* Mobile logo */}
          <div className="lg:hidden mb-8 flex justify-center">
            {branding?.logoUrl ? (
              <div className="flex items-center gap-3">
                <img
                  src={branding.logoUrl}
                  alt={branding.name}
                  className="h-12 w-12 rounded-2xl object-contain"
                />
                <span className="text-xl font-bold text-gray-50">
                  {branding.name}
                </span>
              </div>
            ) : (
              <PlatformLogo />
            )}
          </div>

          {/* Title */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-50">{title}</h1>
            {subtitle && (
              <p className="text-sm text-gray-400 mt-1">{subtitle}</p>
            )}
          </div>

          {/* Form card */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-2xl shadow-black/30">
            {children}
          </div>

          {/* Footer */}
          {footer && (
            <div className="mt-4 text-center text-sm text-gray-500">
              {footer}
            </div>
          )}

          {/* Bottom branding on mobile */}
          <div className="mt-8 text-center lg:hidden">
            <Link
              to="/login"
              className="text-xs text-gray-600 hover:text-gray-500 transition-colors"
            >
              Powered by SubFlow
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
