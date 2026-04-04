import React, { useState } from 'react';
import { Search, UserPlus, Check } from 'lucide-react';
import { SearchInput, PageLoader } from '@/components/ui';
import { useCustomerSearch } from '@/hooks/useSubscriptions';
import type { WizardFormData, Customer } from '@/types/subscription';

interface StepCustomerProps {
  formData: WizardFormData;
  setData: (data: Partial<WizardFormData>) => void;
}

export const StepCustomer: React.FC<StepCustomerProps> = ({
  formData,
  setData,
}) => {
  const [search, setSearch] = useState('');
  const { data: customers, isLoading } = useCustomerSearch(search);

  const handleSelect = (customer: Customer) => {
    setData({ customerId: customer.id, customerName: customer.name });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">Select Customer</h2>
        <p className="mt-1 text-sm text-gray-400">
          Search for an existing customer to create a subscription.
        </p>
      </div>

      <SearchInput
        value={search}
        onChange={setSearch}
        placeholder="Search customers by name or email…"
        debounceMs={400}
      />

      {/* Selected customer card */}
      {formData.customerId && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-violet-600/10
                        border border-violet-500/30 transition-all animate-fade-in">
          <div className="h-10 w-10 rounded-full bg-violet-600/20 flex items-center justify-center">
            <Check className="h-5 w-5 text-violet-400" />
          </div>
          <div>
            <p className="font-medium text-gray-100">{formData.customerName}</p>
            <p className="text-xs text-gray-400">Selected customer</p>
          </div>
        </div>
      )}

      {/* Results */}
      {isLoading && search.length >= 2 && <PageLoader />}

      {customers && customers.length > 0 && (
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {customers.map((customer) => (
            <button
              key={customer.id}
              type="button"
              onClick={() => handleSelect(customer)}
              className={`
                w-full flex items-center gap-3 p-3 rounded-lg text-left
                transition-all duration-200
                ${formData.customerId === customer.id
                  ? 'bg-violet-600/10 border border-violet-500/30'
                  : 'bg-gray-900 border border-gray-800 hover:border-gray-700 hover:bg-gray-800/50'
                }
              `.trim()}
            >
              <div className="h-9 w-9 rounded-full bg-gray-800 flex items-center justify-center
                              text-sm font-bold text-gray-400 shrink-0">
                {customer.name.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-100 truncate">{customer.name}</p>
                <p className="text-xs text-gray-500 truncate">{customer.email}</p>
              </div>
              {formData.customerId === customer.id && (
                <Check className="h-5 w-5 text-violet-400 shrink-0" />
              )}
            </button>
          ))}
        </div>
      )}

      {customers && customers.length === 0 && search.length >= 2 && (
        <div className="text-center py-8 space-y-3">
          <Search className="h-8 w-8 text-gray-700 mx-auto" />
          <p className="text-sm text-gray-400">No customers found for "{search}"</p>
          <button
            type="button"
            className="inline-flex items-center gap-2 text-sm text-violet-400
                       hover:text-violet-300 transition-colors"
          >
            <UserPlus className="h-4 w-4" />
            Invite new customer
          </button>
        </div>
      )}
    </div>
  );
};
