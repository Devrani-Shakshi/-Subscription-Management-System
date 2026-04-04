import React, { useState, useCallback } from 'react';
import { Plus, Trash2, Package } from 'lucide-react';
import { SearchInput, Button } from '@/components/ui';
import { useProductSearch } from '@/hooks/useSubscriptions';
import { formatCurrency } from '@/lib/utils';
import type { WizardFormData, WizardProduct, Product } from '@/types/subscription';

interface StepProductsProps {
  formData: WizardFormData;
  setData: (data: Partial<WizardFormData>) => void;
}

export const StepProducts: React.FC<StepProductsProps> = ({
  formData,
  setData,
}) => {
  const [search, setSearch] = useState('');
  const { data: results } = useProductSearch(search);

  const addProduct = useCallback(
    (product: Product) => {
      const exists = formData.products.find((p) => p.productId === product.id);
      if (exists) return;
      setData({
        products: [
          ...formData.products,
          {
            productId: product.id,
            productName: product.name,
            quantity: 1,
            unitPrice: product.unitPrice,
          },
        ],
      });
      setSearch('');
    },
    [formData.products, setData]
  );

  const removeProduct = useCallback(
    (productId: string) => {
      setData({
        products: formData.products.filter((p) => p.productId !== productId),
      });
    },
    [formData.products, setData]
  );

  const updateProduct = useCallback(
    (productId: string, field: keyof WizardProduct, value: number) => {
      setData({
        products: formData.products.map((p) =>
          p.productId === productId ? { ...p, [field]: value } : p
        ),
      });
    },
    [formData.products, setData]
  );

  const total = formData.products.reduce(
    (sum, p) => sum + p.quantity * p.unitPrice,
    0
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">Add Products</h2>
        <p className="mt-1 text-sm text-gray-400">
          Search and add products to include in the subscription.
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search products…"
          debounceMs={300}
        />

        {results && results.length > 0 && search && (
          <div className="absolute z-20 top-full mt-1 w-full bg-gray-900 border border-gray-800
                          rounded-lg shadow-xl shadow-black/40 max-h-48 overflow-y-auto">
            {results.map((product) => {
              const alreadyAdded = formData.products.some(
                (p) => p.productId === product.id
              );
              return (
                <button
                  key={product.id}
                  type="button"
                  disabled={alreadyAdded}
                  onClick={() => addProduct(product)}
                  className="w-full flex items-center justify-between gap-3 px-4 py-2.5
                             text-sm text-left hover:bg-gray-800/50 disabled:opacity-40
                             disabled:cursor-not-allowed transition-colors"
                >
                  <div className="min-w-0">
                    <p className="text-gray-100 truncate">{product.name}</p>
                    <p className="text-xs text-gray-500">{product.sku}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-gray-400 text-sm">
                      {formatCurrency(product.unitPrice)}
                    </span>
                    {!alreadyAdded && <Plus className="h-4 w-4 text-violet-400" />}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Added products table */}
      {formData.products.length > 0 ? (
        <div className="rounded-xl border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900/50">
                <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-400 uppercase">
                  Product
                </th>
                <th className="px-4 py-2.5 text-center text-xs font-semibold text-gray-400 uppercase w-24">
                  Qty
                </th>
                <th className="px-4 py-2.5 text-right text-xs font-semibold text-gray-400 uppercase w-32">
                  Unit Price
                </th>
                <th className="px-4 py-2.5 text-right text-xs font-semibold text-gray-400 uppercase w-28">
                  Total
                </th>
                <th className="w-12" />
              </tr>
            </thead>
            <tbody>
              {formData.products.map((p) => (
                <tr key={p.productId} className="border-b border-gray-800/30 last:border-0">
                  <td className="px-4 py-3 text-gray-200">{p.productName}</td>
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      min={1}
                      value={p.quantity}
                      onChange={(e) =>
                        updateProduct(p.productId, 'quantity', Number(e.target.value) || 1)
                      }
                      className="w-16 mx-auto block bg-gray-800 border border-gray-700
                                 rounded-md px-2 py-1 text-sm text-gray-100 text-center
                                 focus:outline-none focus:ring-1 focus:ring-violet-500"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      min={0}
                      step={0.01}
                      value={p.unitPrice}
                      onChange={(e) =>
                        updateProduct(p.productId, 'unitPrice', Number(e.target.value) || 0)
                      }
                      className="w-24 ml-auto block bg-gray-800 border border-gray-700
                                 rounded-md px-2 py-1 text-sm text-gray-100 text-right
                                 focus:outline-none focus:ring-1 focus:ring-violet-500"
                    />
                  </td>
                  <td className="px-4 py-3 text-right text-gray-200 font-medium">
                    {formatCurrency(p.quantity * p.unitPrice)}
                  </td>
                  <td className="px-2 py-3">
                    <button
                      type="button"
                      onClick={() => removeProduct(p.productId)}
                      className="h-8 w-8 flex items-center justify-center rounded-lg
                                 text-gray-500 hover:text-red-400 hover:bg-red-500/10
                                 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Total row */}
          <div className="flex items-center justify-between px-4 py-3 bg-gray-900/30
                          border-t border-gray-800">
            <span className="text-sm font-medium text-gray-400">Running Total</span>
            <span className="text-lg font-bold text-emerald-400">
              {formatCurrency(total)}
            </span>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Package className="h-10 w-10 text-gray-700 mb-3" />
          <p className="text-sm text-gray-500">No products added yet</p>
          <p className="text-xs text-gray-600 mt-1">
            Search above to add products to this subscription
          </p>
        </div>
      )}
    </div>
  );
};
