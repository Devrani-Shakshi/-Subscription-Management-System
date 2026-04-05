DO $$
DECLARE
  v_tenant_id uuid;
  v_owner_id uuid;
  v_tenant_idx int;
  v_product_id uuid;
  v_plan_id uuid;
  v_tax_id uuid;
  v_discount_id uuid;
  v_sub_id uuid;
  v_inv_id uuid;
  v_session_id uuid;
  v_admin_id uuid;
BEGIN
    v_admin_id := gen_random_uuid();
    -- Super Admin
    INSERT INTO users (id, email, password_hash, role, name, tenant_id, created_at)
    VALUES (v_admin_id, 'admin_new@subflow.io', '$2b$12$s4KEiWrdmG1ymG2kWH0Z7.NzUX1WAPOzjyV8q8.YG8BcRyDbxaeT2', 'super_admin', 'New Admin', NULL, now())
    ON CONFLICT DO NOTHING;

    FOR v_tenant_idx IN 1..20 LOOP
        v_tenant_id := gen_random_uuid();
        v_owner_id := gen_random_uuid();
        
        -- Insert tenant
        INSERT INTO tenants (id, name, slug, status, created_at)
        VALUES (v_tenant_id, 'Tenant ' || v_tenant_idx, 'tenant-loop-' || v_tenant_idx || '-' || gen_random_uuid(), 'active', now());
        
        -- Insert Owner User
        INSERT INTO users (id, email, password_hash, role, name, tenant_id, created_at)
        VALUES (v_owner_id, 'owner' || v_tenant_idx || '_' || gen_random_uuid() || '@acme.com', '$2b$12$s4KEiWrdmG1ymG2kWH0Z7.NzUX1WAPOzjyV8q8.YG8BcRyDbxaeT2', 'company', 'Owner ' || v_tenant_idx, v_tenant_id, now());
        
        -- Update tenant owner
        UPDATE tenants SET owner_user_id = v_owner_id WHERE id = v_tenant_id;
        
        -- Portal user
        INSERT INTO users (id, email, password_hash, role, name, tenant_id, created_at)
        VALUES (gen_random_uuid(), 'portal' || v_tenant_idx || '_' || gen_random_uuid() || '@acme.com', '$2b$12$s4KEiWrdmG1ymG2kWH0Z7.NzUX1WAPOzjyV8q8.YG8BcRyDbxaeT2', 'portal_user', 'Portal user ' || v_tenant_idx, v_tenant_id, now());

        -- Product
        v_product_id := gen_random_uuid();
        INSERT INTO products (id, tenant_id, name, type, sales_price, cost_price, created_at)
        VALUES (v_product_id, v_tenant_id, 'Prod ' || v_tenant_idx, 'service', (v_tenant_idx * 10), (v_tenant_idx * 5), now());

        -- Product variant
        INSERT INTO product_variants (id, tenant_id, product_id, attribute, value, extra_price, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_product_id, 'Color', 'Red', 0, now());

        -- Tax
        v_tax_id := gen_random_uuid();
        INSERT INTO taxes (id, tenant_id, name, rate, type, created_at)
        VALUES (v_tax_id, v_tenant_id, 'Tax ' || v_tenant_idx, 10, 'percentage', now());

        -- Discount
        v_discount_id := gen_random_uuid();
        INSERT INTO discounts (id, tenant_id, name, type, value, min_purchase, min_qty, start_date, end_date, usage_limit, used_count, applies_to, created_at)
        VALUES (v_discount_id, v_tenant_id, 'Discount ' || v_tenant_idx, 'percent', 10, 0, 1, current_date, current_date + 30, 100, 0, 'subscription', now());

        -- Plan
        v_plan_id := gen_random_uuid();
        INSERT INTO plans (id, tenant_id, name, price, billing_period, min_qty, start_date, features_json, flags_json, created_at)
        VALUES (v_plan_id, v_tenant_id, 'Plan ' || v_tenant_idx, (v_tenant_idx * 15), 'monthly', 1, current_date - 10, '{}', '{}', now());

        -- Subscription
        v_sub_id := gen_random_uuid();
        INSERT INTO subscriptions (id, tenant_id, number, customer_id, plan_id, start_date, expiry_date, payment_terms, status, discount_id, created_at)
        VALUES (v_sub_id, v_tenant_id, 'SUB-' || v_tenant_idx, v_owner_id, v_plan_id, current_date, current_date + 30, 'net-30', 'active', v_discount_id, now());

        -- Subscription Line
        INSERT INTO subscription_lines (id, tenant_id, subscription_id, product_id, qty, unit_price, tax_ids, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_sub_id, v_product_id, 1, (v_tenant_idx * 10), ARRAY[v_tax_id]::uuid[], now());

        -- Invoice
        v_inv_id := gen_random_uuid();
        INSERT INTO invoices (id, tenant_id, invoice_number, subscription_id, customer_id, status, due_date, subtotal, tax_total, discount_total, total, amount_paid, created_at)
        VALUES (v_inv_id, v_tenant_id, 'INV-' || v_tenant_idx, v_sub_id, v_owner_id, 'paid', current_date + 10, 100, 10, 10, 100, 100, now());

        -- Invoice Line
        INSERT INTO invoice_lines (id, tenant_id, invoice_id, product_id, qty, unit_price, tax_id, discount_id, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_inv_id, v_product_id, 1, 100, v_tax_id, v_discount_id, now());

        -- Payment
        INSERT INTO payments (id, tenant_id, invoice_id, customer_id, method, amount, paid_at, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_inv_id, v_owner_id, 'card', 100, now(), now());

        -- Session
        v_session_id := gen_random_uuid();
        INSERT INTO sessions (id, user_id, tenant_id, refresh_token_hash, family_id, device_fingerprint, ip_subnet, expires_at, revoked_at, created_at)
        VALUES (v_session_id, v_owner_id, v_tenant_id, 'hash_' || v_tenant_idx, gen_random_uuid(), 'browser-' || v_tenant_idx, '192.168.0.0/24', now() + interval '7 days', NULL, now());

        -- Audit Log
        INSERT INTO audit_log (id, tenant_id, actor_id, actor_role, entity_type, entity_id, action, diff_json, session_id, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_owner_id, 'company', 'tenant', v_tenant_id, 'create', '{}', v_session_id, now());

        -- Dunning Schedule
        INSERT INTO dunning_schedules (id, tenant_id, invoice_id, attempt_number, action, channel, scheduled_at, status, result_json, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_inv_id, 1, 'retry', 'email', now() + interval '1 day', 'pending', '{}', now());

        -- Churn Score
        INSERT INTO churn_scores (id, tenant_id, customer_id, score, signals_json, computed_at, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_owner_id, 10, '{}', now(), now());

        -- Revenue Recognition
        INSERT INTO revenue_recognition (id, tenant_id, invoice_id, recognized_amount, recognition_date, period, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_inv_id, 100, current_date, '2026-04', now());

        -- Quotation Template
        INSERT INTO quotation_templates (id, tenant_id, name, validity_days, plan_id, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, 'Quotation ' || v_tenant_idx, 30, v_plan_id, now());

    END LOOP;
END $$;
