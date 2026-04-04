import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldX, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui';

export const UnauthorizedPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-dvh flex items-center justify-center bg-gray-950 px-4">
      <div className="text-center max-w-md">
        <div className="h-20 w-20 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-6">
          <ShieldX className="h-10 w-10 text-red-400" />
        </div>
        <h1 className="text-3xl font-bold text-gray-50 mb-2">Access Denied</h1>
        <p className="text-gray-400 mb-8">
          You don&apos;t have permission to access this page. Contact your
          administrator if you believe this is a mistake.
        </p>
        <Button
          variant="secondary"
          icon={<ArrowLeft className="h-4 w-4" />}
          onClick={() => navigate(-1)}
        >
          Go back
        </Button>
      </div>
    </div>
  );
};
