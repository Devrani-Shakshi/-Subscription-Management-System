import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileQuestion, ArrowLeft, LayoutDashboard } from 'lucide-react';
import { Button } from '@/components/ui';
import { useAuthStore } from '@/stores/authStore';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const dashboardPath = user?.role === 'super_admin'
    ? '/admin'
    : user?.role === 'company'
    ? '/company'
    : user?.role === 'portal_user'
    ? '/portal'
    : '/login';

  return (
    <div className="min-h-dvh flex items-center justify-center bg-gray-950 px-4">
      <div className="text-center max-w-md">
        <div className="h-20 w-20 rounded-2xl bg-violet-500/10 border border-violet-500/20
                        flex items-center justify-center mx-auto mb-6">
          <FileQuestion className="h-10 w-10 text-violet-400" />
        </div>

        <p className="text-7xl font-black text-gray-800 mb-4 select-none">404</p>

        <h1 className="text-2xl font-bold text-gray-50 mb-2">Page not found</h1>
        <p className="text-gray-400 mb-8">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>

        <div className="flex items-center justify-center gap-3">
          <Button
            variant="secondary"
            icon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => navigate(-1)}
          >
            Go back
          </Button>
          <Button
            icon={<LayoutDashboard className="h-4 w-4" />}
            onClick={() => navigate(dashboardPath)}
          >
            Go to dashboard
          </Button>
        </div>
      </div>
    </div>
  );
};
