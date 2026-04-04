import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader, PageLoader, PageError } from '@/components/ui';
import { usePortalProfile } from '@/hooks/usePortal';
import { PersonalInfoSection } from './ProfilePersonalInfo';
import { ChangePasswordSection } from './ProfileChangePassword';
import { ActiveSessionsSection } from './ProfileActiveSessions';
import { DangerZoneSection } from './ProfileDangerZone';

export const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { data: profile, isLoading, isError, refetch } = usePortalProfile();

  if (isLoading) return <PageLoader />;
  if (isError) return <PageError onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader title="My Profile" />

      <div className="max-w-xl mx-auto space-y-5">
        {/* Personal info */}
        {profile && <PersonalInfoSection profile={profile} />}

        {/* Change password */}
        <ChangePasswordSection />

        {/* Active sessions */}
        <ActiveSessionsSection />

        {/* Danger zone */}
        <DangerZoneSection onNavigate={() => navigate('/portal/my-subscription')} />
      </div>
    </div>
  );
};
