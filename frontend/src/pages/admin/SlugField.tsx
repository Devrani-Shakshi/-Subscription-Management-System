import React from 'react';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { UseFormRegister } from 'react-hook-form';
import { FormField, Input } from '@/components/ui';
import type { SlugCheckResponse } from '@/types/admin';

interface SlugFieldProps {
  slug: string;
  error?: string;
  register: UseFormRegister<{ companyName: string; slug: string; ownerEmail: string }>;
  onSlugEdit: () => void;
  checking: boolean;
  slugCheck: SlugCheckResponse | undefined;
}

export const SlugField: React.FC<SlugFieldProps> = ({
  slug,
  error,
  register,
  onSlugEdit,
  checking,
  slugCheck,
}) => (
  <FormField label="URL slug" name="create-slug" error={error} required>
    <div className="relative">
      <Input
        id="create-slug"
        placeholder="acme-corp"
        error={!!error}
        className="pr-10"
        {...register('slug', { onChange: () => onSlugEdit() })}
      />
      <div className="absolute right-3 top-1/2 -translate-y-1/2">
        {checking ? (
          <Loader2 className="h-4 w-4 text-gray-500 animate-spin" />
        ) : slugCheck?.available === true ? (
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
        ) : slugCheck?.available === false ? (
          <XCircle className="h-4 w-4 text-red-400" />
        ) : null}
      </div>
    </div>
    {slug && (
      <p className="text-xs text-gray-500 mt-1">
        app.subflow.io/<span className="text-gray-300">{slug}</span>
      </p>
    )}
  </FormField>
);
