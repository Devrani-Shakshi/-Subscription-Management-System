import { z } from 'zod';
import { passwordPolicy } from './validations';

export const profileSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email(),
  street: z.string().optional().default(''),
  city: z.string().optional().default(''),
  state: z.string().optional().default(''),
  country: z.string().optional().default(''),
  zip: z.string().optional().default(''),
});

export const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: passwordPolicy,
    confirmPassword: z.string().min(1, 'Confirm your new password'),
  })
  .refine((d) => d.newPassword === d.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

export const paymentSchema = z.object({
  cardNumber: z
    .string()
    .min(19, 'Enter a valid card number')
    .max(19, 'Enter a valid card number'),
  expiry: z
    .string()
    .regex(/^(0[1-9]|1[0-2])\/\d{2}$/, 'Use MM/YY format'),
  cvv: z
    .string()
    .min(3, 'CVV too short')
    .max(4, 'CVV too long'),
  cardholderName: z.string().min(2, 'Cardholder name is required'),
});

export type ProfileFormData = z.infer<typeof profileSchema>;
export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;
export type PaymentFormData = z.infer<typeof paymentSchema>;
