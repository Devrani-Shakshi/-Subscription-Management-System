import React, { useState, useEffect, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { AxiosError } from 'axios';
import { Building2 } from 'lucide-react';
import { useCreateCompany, useCheckSlug } from '@/hooks/useAdmin';
import { Modal, Button, FormField, Input } from '@/components/ui';
import { SlugField } from './SlugField';
import type { ApiResponse } from '@/types';

const schema = z.object({
  companyName: z.string().min(2, 'At least 2 characters'),
  slug: z.string().min(2, 'At least 2 characters').regex(/^[a-z0-9-]+$/, 'Lowercase letters, numbers, hyphens only'),
  ownerEmail: z.string().email('Enter a valid email'),
});

type FormData = z.infer<typeof schema>;

function slugify(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

interface CreateCompanyModalProps {
  open: boolean;
  onClose: () => void;
}

export const CreateCompanyModal: React.FC<CreateCompanyModalProps> = ({ open, onClose }) => {
  const createMutation = useCreateCompany();
  const [slugEdited, setSlugEdited] = useState(false);
  const [debouncedSlug, setDebouncedSlug] = useState('');

  const { register, handleSubmit, watch, setValue, setError, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { companyName: '', slug: '', ownerEmail: '' },
  });

  const companyName = watch('companyName');
  const slug = watch('slug');

  useEffect(() => {
    if (!slugEdited && companyName) setValue('slug', slugify(companyName));
  }, [companyName, slugEdited, setValue]);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSlug(slug), 400);
    return () => clearTimeout(timer);
  }, [slug]);

  const { data: slugCheck, isFetching: checkingSlug } = useCheckSlug(debouncedSlug);

  const onSubmit = useCallback(async (data: FormData) => {
    createMutation.mutate(data, {
      onSuccess: () => { reset(); setSlugEdited(false); onClose(); },
      onError: (error) => {
        const axiosErr = error as AxiosError<ApiResponse<never>>;
        if (axiosErr.response?.status === 409) {
          const responseData = axiosErr.response.data as unknown as Record<string, string>;
          setError('slug', { message: `URL taken.${responseData.suggested ? ` Try '${responseData.suggested}'.` : ''}` });
        }
      },
    });
  }, [createMutation, onClose, reset, setError]);

  const handleClose = useCallback(() => { reset(); setSlugEdited(false); onClose(); }, [onClose, reset]);

  return (
    <Modal open={open} onClose={handleClose} title="Create company" size="md" footer={
      <>
        <Button variant="ghost" onClick={handleClose} disabled={createMutation.isPending}>Cancel</Button>
        <Button variant="primary" onClick={handleSubmit(onSubmit)} loading={createMutation.isPending} icon={<Building2 className="h-4 w-4" />}>Create</Button>
      </>
    }>
      <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
        <FormField label="Company name" name="create-name" error={errors.companyName?.message} required>
          <Input id="create-name" placeholder="Acme Corp" error={!!errors.companyName} {...register('companyName')} />
        </FormField>

        <SlugField slug={slug} error={errors.slug?.message} register={register} onSlugEdit={() => setSlugEdited(true)} checking={checkingSlug} slugCheck={slugCheck} />

        <FormField label="Owner email" name="create-email" error={errors.ownerEmail?.message} required>
          <Input id="create-email" type="email" placeholder="owner@acme.com" error={!!errors.ownerEmail} {...register('ownerEmail')} />
        </FormField>
      </form>
    </Modal>
  );
};
