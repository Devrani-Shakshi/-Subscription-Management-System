import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDeleteCompany } from '@/hooks/useAdmin';
import { Modal, Button, Input, FormField } from '@/components/ui';
import type { AdminCompanySummary } from '@/types/admin';

interface DeleteCompanyModalProps {
  company: AdminCompanySummary;
  open: boolean;
  onClose: () => void;
}

export const DeleteCompanyModal: React.FC<DeleteCompanyModalProps> = ({
  company,
  open,
  onClose,
}) => {
  const navigate = useNavigate();
  const deleteMutation = useDeleteCompany();
  const [confirmText, setConfirmText] = useState('');

  const canDelete = !company.hasActiveSubscriptions;
  const confirmed = confirmText === company.name;

  const handleDelete = useCallback(() => {
    if (!confirmed) return;
    deleteMutation.mutate(company.id, {
      onSuccess: () => {
        onClose();
        navigate('/admin/companies');
      },
    });
  }, [company.id, confirmed, deleteMutation, navigate, onClose]);

  const handleClose = useCallback(() => {
    setConfirmText('');
    onClose();
  }, [onClose]);

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Delete company"
      size="sm"
      footer={
        canDelete ? (
          <>
            <Button variant="ghost" onClick={handleClose} disabled={deleteMutation.isPending}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
              loading={deleteMutation.isPending}
              disabled={!confirmed}
            >
              Delete permanently
            </Button>
          </>
        ) : (
          <Button variant="secondary" onClick={handleClose}>
            Close
          </Button>
        )
      }
    >
      {canDelete ? (
        <div className="space-y-4">
          <p className="text-sm text-gray-300 leading-relaxed">
            This will permanently delete{' '}
            <span className="font-semibold text-gray-100">{company.name}</span>{' '}
            and all associated data. This action cannot be undone.
          </p>
          <FormField
            label={`Type "${company.name}" to confirm`}
            name="delete-confirm"
          >
            <Input
              id="delete-confirm"
              placeholder={company.name}
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              error={confirmText.length > 0 && !confirmed}
            />
          </FormField>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
            <svg className="h-5 w-5 text-amber-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <p className="text-sm text-amber-300">
              Cannot delete this company. Cancel all active subscriptions first.
            </p>
          </div>
          <p className="text-sm text-gray-400">
            <span className="font-semibold text-gray-200">{company.name}</span>{' '}
            has {company.activeSubs} active subscription{company.activeSubs !== 1 ? 's' : ''}.
          </p>
        </div>
      )}
    </Modal>
  );
};
