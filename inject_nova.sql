DO $$
DECLARE
  v_tenant_id uuid := gen_random_uuid();
  v_owner_id uuid := gen_random_uuid();
  v_product_id uuid;
  v_plan_id uuid;
  v_tax_id uuid;
  v_discount_id uuid;
  v_sub_id uuid;
  v_inv_id uuid;
  v_session_id uuid;
  v_customer_id uuid;
  i int;
BEGIN
    -- Insert tenant
    INSERT INTO tenants (id, name, slug, status, created_at)
    VALUES (v_tenant_id, 'Demodata Company', 'demodata-company', 'active', now());
    
    -- Insert Owner User
    INSERT INTO users (id, email, password_hash, role, name, tenant_id, created_at)
    VALUES (v_owner_id, 'demo@demodata.com', '$2b$12$s4KEiWrdmG1ymG2kWH0Z7.NzUX1WAPOzjyV8q8.YG8BcRyDbxaeT2', 'company', 'Demo User', v_tenant_id, now());
    
    -- Update tenant owner
    UPDATE tenants SET owner_user_id = v_owner_id WHERE id = v_tenant_id;
    
    -- Tax
    v_tax_id := gen_random_uuid();
    INSERT INTO taxes (id, tenant_id, name, rate, type, created_at)
    VALUES (v_tax_id, v_tenant_id, 'Standard Tax', 10, 'percentage', now());

    -- Discount
    v_discount_id := gen_random_uuid();
    INSERT INTO discounts (id, tenant_id, name, type, value, min_purchase, min_qty, start_date, end_date, usage_limit, used_count, applies_to, created_at)
    VALUES (v_discount_id, v_tenant_id, 'Welcome Promo', 'percent', 10, 0, 1, current_date, current_date + 300, 1000, 0, 'subscription', now());

    FOR i IN 1..50 LOOP
        -- Portal / Customer user
        v_customer_id := gen_random_uuid();
        INSERT INTO users (id, email, password_hash, role, name, tenant_id, created_at)
        VALUES (v_customer_id, 'customer_' || gen_random_uuid() || '@fake.com', '$2b$12$s4KEiWrdmG1ymG2kWH0Z7.NzUX1WAPOzjyV8q8.YG8BcRyDbxaeT2', 'portal_user', 'Customer ' || i, v_tenant_id, now());

        -- Product
        v_product_id := gen_random_uuid();
        INSERT INTO products (id, tenant_id, name, type, sales_price, cost_price, created_at)
        VALUES (v_product_id, v_tenant_id, 'Product Series ' || i, 'service', (i * 10), (i * 2), now());

        -- Product variant
        INSERT INTO product_variants (id, tenant_id, product_id, attribute, value, extra_price, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_product_id, 'Size', 'Large', 5, now());

        -- Plan
        v_plan_id := gen_random_uuid();
        INSERT INTO plans (id, tenant_id, name, price, billing_period, min_qty, start_date, features_json, flags_json, created_at)
        VALUES (v_plan_id, v_tenant_id, 'Plan Track ' || i, (i * 15), 'monthly', 1, current_date - 10, '{}', '{}', now());

        -- Subscription
        v_sub_id := gen_random_uuid();
        INSERT INTO subscriptions (id, tenant_id, number, customer_id, plan_id, start_date, expiry_date, payment_terms, status, discount_id, created_at)
        VALUES (v_sub_id, v_tenant_id, 'SUB-X-' || gen_random_uuid(), v_customer_id, v_plan_id, current_date, current_date + 30, 'net-30', 'active', v_discount_id, now());

        -- Subscription Line
        INSERT INTO subscription_lines (id, tenant_id, subscription_id, product_id, qty, unit_price, tax_ids, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_sub_id, v_product_id, 1, (i * 10), ARRAY[v_tax_id]::uuid[], now());

        -- Invoice
        v_inv_id := gen_random_uuid();
        INSERT INTO invoices (id, tenant_id, invoice_number, subscription_id, customer_id, status, due_date, subtotal, tax_total, discount_total, total, amount_paid, created_at)
        VALUES (v_inv_id, v_tenant_id, 'INV-X-' || gen_random_uuid(), v_sub_id, v_customer_id, 'paid', current_date + 10, 100, 10, 10, 100, 100, now());

        -- Invoice Line
        INSERT INTO invoice_lines (id, tenant_id, invoice_id, product_id, qty, unit_price, tax_id, discount_id, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_inv_id, v_product_id, 1, 100, v_tax_id, v_discount_id, now());

        -- Payment
        INSERT INTO payments (id, tenant_id, invoice_id, customer_id, method, amount, paid_at, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_inv_id, v_customer_id, 'card', 100, now(), now());

        -- Session
        v_session_id := gen_random_uuid();
        INSERT INTO sessions (id, user_id, tenant_id, refresh_token_hash, family_id, device_fingerprint, ip_subnet, expires_at, revoked_at, created_at)
        VALUES (v_session_id, v_owner_id, v_tenant_id, 'hash_' || gen_random_uuid(), gen_random_uuid(), 'browser', '192.168.0.0/24', now() + interval '7 days', NULL, now());

        -- Audit Log
        INSERT INTO audit_log (id, tenant_id, actor_id, actor_role, entity_type, entity_id, action, diff_json, session_id, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_owner_id, 'company', 'product', v_product_id, 'create', '{}', v_session_id, now());

        -- Dunning Schedule
        INSERT INTO dunning_schedules (id, tenant_id, invoice_id, attempt_number, action, channel, scheduled_at, status, result_json, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_inv_id, 1, 'retry', 'email', now() + interval '1 day', 'pending', '{}', now());

        -- Churn Score
        INSERT INTO churn_scores (id, tenant_id, customer_id, score, signals_json, computed_at, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_customer_id, 25, '{}', now(), now());

        -- Revenue Recognition
        INSERT INTO revenue_recognition (id, tenant_id, invoice_id, recognized_amount, recognition_date, period, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, v_inv_id, 100, current_date, '2026-04', now());

        -- Quotation Template
        INSERT INTO quotation_templates (id, tenant_id, name, validity_days, plan_id, created_at)
        VALUES (gen_random_uuid(), v_tenant_id, 'Quotation ' || gen_random_uuid(), 30, v_plan_id, now());

    END LOOP;
END $$;
