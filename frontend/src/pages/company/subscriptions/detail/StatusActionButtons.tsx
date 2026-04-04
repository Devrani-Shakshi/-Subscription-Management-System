import React from 'react';
import { Button } from '@/components/ui';
import {
  Send,
  CheckCircle2,
  Play,
  XCircle,
  TrendingUp,
  TrendingDown,
  Pause,
  RotateCcw,
  Trash2,
} from 'lucide-react';
import type { SubscriptionStatus } from '@/types/subscription';

interface StatusActionButtonsProps {
  status: SubscriptionStatus;
  pausable: boolean;
  renewable: boolean;
  onTransition: (to: SubscriptionStatus, label: string, variant: 'primary' | 'danger') => void;
  onUpgrade: () => void;
  onDowngrade: () => void;
  onDelete: () => void;
}

export const StatusActionButtons: React.FC<StatusActionButtonsProps> = ({
  status,
  pausable,
  renewable,
  onTransition,
  onUpgrade,
  onDowngrade,
  onDelete,
}) => {
  switch (status) {
    case 'draft':
      return (
        <>
          <Button
            variant="primary"
            size="sm"
            icon={<Send className="h-4 w-4" />}
            onClick={() => onTransition('quotation', 'Send quotation?', 'primary')}
          >
            Send quotation
          </Button>
          <Button
            variant="danger"
            size="sm"
            icon={<Trash2 className="h-4 w-4" />}
            onClick={onDelete}
          >
            Delete
          </Button>
        </>
      );

    case 'quotation':
      return (
        <>
          <Button
            variant="primary"
            size="sm"
            icon={<CheckCircle2 className="h-4 w-4" />}
            onClick={() => onTransition('confirmed', 'Confirm this subscription?', 'primary')}
          >
            Confirm
          </Button>
          <Button
            variant="danger"
            size="sm"
            icon={<XCircle className="h-4 w-4" />}
            onClick={() => onTransition('cancelled', 'Cancel this quotation?', 'danger')}
          >
            Cancel
          </Button>
        </>
      );

    case 'confirmed':
      return (
        <>
          <Button
            variant="teal"
            size="sm"
            icon={<Play className="h-4 w-4" />}
            onClick={() => onTransition('active', 'Activate subscription?', 'primary')}
          >
            Activate
          </Button>
          <Button
            variant="danger"
            size="sm"
            icon={<XCircle className="h-4 w-4" />}
            onClick={() => onTransition('cancelled', 'Cancel confirmed subscription?', 'danger')}
          >
            Cancel
          </Button>
        </>
      );

    case 'active':
      return (
        <>
          <Button
            variant="primary"
            size="sm"
            icon={<TrendingUp className="h-4 w-4" />}
            onClick={onUpgrade}
          >
            Upgrade
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<TrendingDown className="h-4 w-4" />}
            onClick={onDowngrade}
          >
            Downgrade
          </Button>
          {pausable && (
            <Button
              variant="amber"
              size="sm"
              icon={<Pause className="h-4 w-4" />}
              onClick={() => onTransition('paused', 'Pause subscription?', 'primary')}
            >
              Pause
            </Button>
          )}
          <Button
            variant="danger"
            size="sm"
            icon={<XCircle className="h-4 w-4" />}
            onClick={() => onTransition('closed', 'Close this subscription?', 'danger')}
          >
            Close
          </Button>
        </>
      );

    case 'closed':
      return renewable ? (
        <Button
          variant="primary"
          size="sm"
          icon={<RotateCcw className="h-4 w-4" />}
          onClick={() => onTransition('active', 'Reactivate subscription?', 'primary')}
        >
          Reactivate
        </Button>
      ) : null;

    default:
      return null;
  }
};
