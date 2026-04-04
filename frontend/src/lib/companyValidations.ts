import { z } from 'zod';

// ── Product ─────────────────────────────────────────────────
const variantSchema = z.object({
  attribute: z.string().min(1, 'Attribute is required'),
  value: z.string().min(1, 'Value is required'),
  extra_price: z.coerce.number().min(0, 'Must be 0 or more'),
});

export const productSchema = z.object({
  name: z.string().min(1, 'Product name is required'),
  type: z.enum(['physical', 'digital', 'service'], {
    required_error: 'Select a product type',
  }),
  sales_price: z.coerce.number().min(0, 'Must be 0 or more'),
  cost_price: z.coerce.number().min(0, 'Must be 0 or more'),
  variants: z.array(variantSchema),
});

export type ProductSchemaType = z.infer<typeof productSchema>;

// ── Plan ────────────────────────────────────────────────────
const featureSchema = z.object({
  key: z.string().min(1, 'Feature name is required'),
  value: z.string().min(1, 'Feature value is required'),
});

export const planSchema = z.object({
  name: z.string().min(1, 'Plan name is required'),
  price: z.coerce.number().min(0, 'Price must be 0 or more'),
  billing_period: z.enum(['daily', 'weekly', 'monthly', 'quarterly', 'yearly'], {
    required_error: 'Select a billing period',
  }),
  min_quantity: z.coerce.number().int().min(1, 'Minimum quantity is 1'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().optional().or(z.literal('')),
  auto_close: z.boolean(),
  closable: z.boolean(),
  pausable: z.boolean(),
  renewable: z.boolean(),
  features_json: z.array(featureSchema),
});

export type PlanSchemaType = z.infer<typeof planSchema>;

// ── Customer Invite ─────────────────────────────────────────
export const inviteCustomerSchema = z.object({
  email: z.string().email('Enter a valid email'),
});

export type InviteCustomerSchemaType = z.infer<typeof inviteCustomerSchema>;

// ── Template ────────────────────────────────────────────────
const productLineSchema = z.object({
  product_id: z.string().min(1, 'Select a product'),
  quantity: z.coerce.number().int().min(1, 'Quantity must be at least 1'),
});

export const templateSchema = z.object({
  name: z.string().min(1, 'Template name is required'),
  validity_days: z.coerce.number().int().min(1, 'Must be at least 1 day'),
  plan_id: z.string().min(1, 'Select a plan'),
  product_lines: z.array(productLineSchema).min(1, 'Add at least one product line'),
});

export type TemplateSchemaType = z.infer<typeof templateSchema>;

// ── Discount ────────────────────────────────────────────────
export const discountSchema = z.object({
  name: z.string().min(1, 'Discount name is required'),
  type: z.enum(['fixed', 'percent']),
  value: z.coerce.number().min(0.01, 'Value must be greater than 0'),
  min_purchase: z.coerce.number().min(0, 'Must be 0 or more'),
  min_quantity: z.coerce.number().int().min(0, 'Must be 0 or more'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().optional().or(z.literal('')),
  usage_limit: z.coerce.number().int().min(0).nullable().optional(),
  applies_to: z.enum(['product', 'subscription']),
});

export type DiscountSchemaType = z.infer<typeof discountSchema>;

// ── Tax ─────────────────────────────────────────────────────
export const taxSchema = z.object({
  name: z.string().min(1, 'Tax name is required'),
  rate: z.coerce
    .number()
    .min(0, 'Rate must be 0 or more')
    .max(100, 'Rate cannot exceed 100'),
  type: z.string().min(1, 'Tax type is required'),
});

export type TaxSchemaType = z.infer<typeof taxSchema>;
