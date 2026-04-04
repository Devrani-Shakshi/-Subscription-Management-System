import React, { useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  CheckCircle, Send, Download, XCircle, Edit, ArrowLeft, CreditCard,
} from 'lucide-react';
import { PageHeader, StatusBadge, Button, PageLoader, PageError } from '@/components/ui';
import { useInvoice, useConfirmInvoice, useSendInvoice, useDownloadInvoicePdf, useCancelInvoice } from '@/hooks/useInvoices';
import { InvoicePaperCard } from './invoices/InvoicePaperCard';
import { PaymentHistoryCard, AuditTimelineCard } from './invoices/InvoiceSidePanels';
import type { InvoicePaymentRecord, InvoiceAuditEntry } from '@/types/billing';

export const InvoiceDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data, isLoading, isError, refetch } = useInvoice(id ?? '');
  const confirm = useConfirmInvoice();
  const send = useSendInvoice();
  const download = useDownloadInvoicePdf();
  const cancel = useCancelInvoice();

  const invoice = data?.data;

  // Mock side-panel data (would normally come from the same API response)
  const payments: InvoicePaymentRecord[] = useMemo(() => {
    if (!invoice || invoice.amountPaid === 0) return [];
    return [
      { id: '1', amount: invoice.amountPaid, method: 'credit_card', date: invoice.updatedAt },
    ];
  }, [invoice]);

  const audit: InvoiceAuditEntry[] = useMemo(() => {
    if (!invoice) return [];
    return [
      { id: '1', action: 'Invoice created', user: 'System', timestamp: invoice.createdAt, details: '' },
      ...(invoice.status !== 'draft'
        ? [{ id: '2', action: 'Invoice confirmed', user: 'Admin', timestamp: invoice.updatedAt, details: '' }]
        : []),
    ];
  }, [invoice]);

  if (isLoading) return <PageLoader />;
  if (isError || !invoice) return <PageError onRetry={refetch} />;

  const status = invoice.status;

  const actions = (
    <>
      {status === 'draft' && (
        <>
          <Button variant="primary" size="sm" icon={<CheckCircle className="h-4 w-4" />}
            loading={confirm.isPending} onClick={() => confirm.mutate(invoice.id)}>Confirm</Button>
          <Button variant="ghost" size="sm" icon={<Edit className="h-4 w-4" />}
            onClick={() => navigate(`/company/invoices/${invoice.id}/edit`)}>Edit</Button>
          <Button variant="danger" size="sm" icon={<XCircle className="h-4 w-4" />}
            loading={cancel.isPending} onClick={() => cancel.mutate(invoice.id)}>Cancel</Button>
        </>
      )}
      {(status === 'confirmed' || status === 'overdue') && (
        <>
          <Button variant="primary" size="sm" icon={<Send className="h-4 w-4" />}
            loading={send.isPending} onClick={() => send.mutate(invoice.id)}>Send</Button>
          <Button variant="secondary" size="sm" icon={<Download className="h-4 w-4" />}
            loading={download.isPending} onClick={() => download.mutate(invoice.id)}>Download PDF</Button>
          <Button variant="danger" size="sm" icon={<XCircle className="h-4 w-4" />}
            loading={cancel.isPending} onClick={() => cancel.mutate(invoice.id)}>Cancel</Button>
        </>
      )}
      {status === 'paid' && (
        <>
          <Button variant="secondary" size="sm" icon={<Download className="h-4 w-4" />}
            loading={download.isPending} onClick={() => download.mutate(invoice.id)}>Download PDF</Button>
          <Button variant="ghost" size="sm" icon={<CreditCard className="h-4 w-4" />}
            onClick={() => navigate('/company/payments')}>View payment</Button>
        </>
      )}
    </>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Invoice ${invoice.number}`}
        subtitle={<StatusBadge status={invoice.status} /> as unknown as string}
        breadcrumbs={[
          { label: 'Invoices', href: '/company/invoices' },
          { label: invoice.number },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" icon={<ArrowLeft className="h-4 w-4" />}
              onClick={() => navigate('/company/invoices')}>Back</Button>
            {actions}
          </div>
        }
      />

      {/* Two column layout — paper card left, panels right */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <InvoicePaperCard invoice={invoice} />
        </div>
        <div className="space-y-6">
          {/* Actions card (mobile visible) */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 xl:hidden">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Actions</h3>
            <div className="flex flex-wrap gap-2">{actions}</div>
          </div>
          <PaymentHistoryCard payments={payments} />
          <AuditTimelineCard entries={audit} />
        </div>
      </div>
    </div>
  );
};
