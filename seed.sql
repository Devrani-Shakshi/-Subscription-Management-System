-- SEED DATA FOR ALL TABLES
-- Password for all users: Password123!
-- Hash: $2b$12$s4KEiWrdmG1ymG2kWH0Z7.NzUX1WAPOzjyV8q8.YG8BcRyDbxaeT2

BEGIN;

-- Fixed UUIDs for FK references
DO $$
DECLARE
  t1 uuid := 'a0000000-0000-0000-0000-000000000001';
  t2 uuid := 'a0000000-0000-0000-0000-000000000002';
  t3 uuid := 'a0000000-0000-0000-0000-000000000003';
  pw text := '$2b$12$s4KEiWrdmG1ymG2kWH0Z7.NzUX1WAPOzjyV8q8.YG8BcRyDbxaeT2';
  -- user ids
  sa uuid := 'b0000000-0000-0000-0000-000000000001';
  c1 uuid := 'b0000000-0000-0000-0000-000000000002';
  c2 uuid := 'b0000000-0000-0000-0000-000000000003';
  c3 uuid := 'b0000000-0000-0000-0000-000000000004';
  p1 uuid := 'c0000000-0000-0000-0000-000000000001';
  p2 uuid := 'c0000000-0000-0000-0000-000000000002';
  p3 uuid := 'c0000000-0000-0000-0000-000000000003';
  p4 uuid := 'c0000000-0000-0000-0000-000000000004';
  p5 uuid := 'c0000000-0000-0000-0000-000000000005';
  p6 uuid := 'c0000000-0000-0000-0000-000000000006';
  p7 uuid := 'c0000000-0000-0000-0000-000000000007';
  p8 uuid := 'c0000000-0000-0000-0000-000000000008';
  -- product ids
  pr1 uuid := 'd0000000-0000-0000-0000-000000000001';
  pr2 uuid := 'd0000000-0000-0000-0000-000000000002';
  pr3 uuid := 'd0000000-0000-0000-0000-000000000003';
  pr4 uuid := 'd0000000-0000-0000-0000-000000000004';
  pr5 uuid := 'd0000000-0000-0000-0000-000000000005';
  pr6 uuid := 'd0000000-0000-0000-0000-000000000006';
  pr7 uuid := 'd0000000-0000-0000-0000-000000000007';
  pr8 uuid := 'd0000000-0000-0000-0000-000000000008';
  pr9 uuid := 'd0000000-0000-0000-0000-000000000009';
  pr10 uuid := 'd0000000-0000-0000-0000-000000000010';
  -- tax ids
  tx1 uuid := 'e0000000-0000-0000-0000-000000000001';
  tx2 uuid := 'e0000000-0000-0000-0000-000000000002';
  tx3 uuid := 'e0000000-0000-0000-0000-000000000003';
  tx4 uuid := 'e0000000-0000-0000-0000-000000000004';
  tx5 uuid := 'e0000000-0000-0000-0000-000000000005';
  -- discount ids
  dc1 uuid := 'e1000000-0000-0000-0000-000000000001';
  dc2 uuid := 'e1000000-0000-0000-0000-000000000002';
  dc3 uuid := 'e1000000-0000-0000-0000-000000000003';
  dc4 uuid := 'e1000000-0000-0000-0000-000000000004';
  dc5 uuid := 'e1000000-0000-0000-0000-000000000005';
  dc6 uuid := 'e1000000-0000-0000-0000-000000000006';
  dc7 uuid := 'e1000000-0000-0000-0000-000000000007';
  dc8 uuid := 'e1000000-0000-0000-0000-000000000008';
  dc9 uuid := 'e1000000-0000-0000-0000-000000000009';
  dc10 uuid := 'e1000000-0000-0000-0000-000000000010';
  -- plan ids
  pl1 uuid := 'f0000000-0000-0000-0000-000000000001';
  pl2 uuid := 'f0000000-0000-0000-0000-000000000002';
  pl3 uuid := 'f0000000-0000-0000-0000-000000000003';
  pl4 uuid := 'f0000000-0000-0000-0000-000000000004';
  pl5 uuid := 'f0000000-0000-0000-0000-000000000005';
  pl6 uuid := 'f0000000-0000-0000-0000-000000000006';
  pl7 uuid := 'f0000000-0000-0000-0000-000000000007';
  pl8 uuid := 'f0000000-0000-0000-0000-000000000008';
  pl9 uuid := 'f0000000-0000-0000-0000-000000000009';
  pl10 uuid := 'f0000000-0000-0000-0000-000000000010';
  -- subscription ids
  s1 uuid := 'f1000000-0000-0000-0000-000000000001';
  s2 uuid := 'f1000000-0000-0000-0000-000000000002';
  s3 uuid := 'f1000000-0000-0000-0000-000000000003';
  s4 uuid := 'f1000000-0000-0000-0000-000000000004';
  s5 uuid := 'f1000000-0000-0000-0000-000000000005';
  s6 uuid := 'f1000000-0000-0000-0000-000000000006';
  s7 uuid := 'f1000000-0000-0000-0000-000000000007';
  s8 uuid := 'f1000000-0000-0000-0000-000000000008';
  s9 uuid := 'f1000000-0000-0000-0000-000000000009';
  s10 uuid := 'f1000000-0000-0000-0000-000000000010';
  -- invoice ids
  i1 uuid := 'f2000000-0000-0000-0000-000000000001';
  i2 uuid := 'f2000000-0000-0000-0000-000000000002';
  i3 uuid := 'f2000000-0000-0000-0000-000000000003';
  i4 uuid := 'f2000000-0000-0000-0000-000000000004';
  i5 uuid := 'f2000000-0000-0000-0000-000000000005';
  i6 uuid := 'f2000000-0000-0000-0000-000000000006';
  i7 uuid := 'f2000000-0000-0000-0000-000000000007';
  i8 uuid := 'f2000000-0000-0000-0000-000000000008';
  i9 uuid := 'f2000000-0000-0000-0000-000000000009';
  i10 uuid := 'f2000000-0000-0000-0000-000000000010';
  -- session ids
  ss1 uuid := 'f3000000-0000-0000-0000-000000000001';
  ss2 uuid := 'f3000000-0000-0000-0000-000000000002';
  ss3 uuid := 'f3000000-0000-0000-0000-000000000003';
  ss4 uuid := 'f3000000-0000-0000-0000-000000000004';
  ss5 uuid := 'f3000000-0000-0000-0000-000000000005';
BEGIN

-- TENANTS
INSERT INTO tenants (id,name,slug,status,created_at) VALUES
(t1,'Acme Corp','acme-corp','active',now()-interval '90 days'),
(t2,'TechNova Solutions','technova','active',now()-interval '60 days'),
(t3,'CloudServe Inc','cloudserve','trial',now()-interval '5 days')
ON CONFLICT DO NOTHING;

-- USERS (1 super_admin, 3 company, 8 portal_user = 12)
INSERT INTO users (id,email,password_hash,role,name,tenant_id,created_at) VALUES
(sa,'admin@subflow.io',pw,'super_admin','Platform Admin',NULL,now()-interval '100 days'),
(c1,'alice@acme.com',pw,'company','Alice Johnson',t1,now()-interval '89 days'),
(c2,'bob@technova.com',pw,'company','Bob Williams',t2,now()-interval '59 days'),
(c3,'carol@cloudserve.com',pw,'company','Carol Davis',t3,now()-interval '4 days'),
(p1,'john.doe@email.com',pw,'portal_user','John Doe',t1,now()-interval '80 days'),
(p2,'jane.smith@email.com',pw,'portal_user','Jane Smith',t1,now()-interval '70 days'),
(p3,'mike.brown@email.com',pw,'portal_user','Mike Brown',t1,now()-interval '60 days'),
(p4,'sarah.wilson@email.com',pw,'portal_user','Sarah Wilson',t1,now()-interval '50 days'),
(p5,'david.lee@email.com',pw,'portal_user','David Lee',t2,now()-interval '55 days'),
(p6,'emma.martinez@email.com',pw,'portal_user','Emma Martinez',t2,now()-interval '45 days'),
(p7,'chris.taylor@email.com',pw,'portal_user','Chris Taylor',t2,now()-interval '35 days'),
(p8,'olivia.anderson@email.com',pw,'portal_user','Olivia Anderson',t3,now()-interval '3 days')
ON CONFLICT DO NOTHING;

-- Set tenant owners
UPDATE tenants SET owner_user_id=c1 WHERE id=t1;
UPDATE tenants SET owner_user_id=c2 WHERE id=t2;
UPDATE tenants SET owner_user_id=c3 WHERE id=t3;

-- PRODUCTS (10)
INSERT INTO products (id,tenant_id,name,type,sales_price,cost_price,created_at) VALUES
(pr1,t1,'Cloud Hosting Basic','service',29.99,15.00,now()-interval '85 days'),
(pr2,t1,'Cloud Hosting Pro','service',79.99,40.00,now()-interval '85 days'),
(pr3,t1,'Cloud Hosting Enterprise','service',199.99,90.00,now()-interval '85 days'),
(pr4,t1,'SSL Certificate','service',9.99,2.00,now()-interval '80 days'),
(pr5,t1,'Domain Registration','service',12.99,5.00,now()-interval '80 days'),
(pr6,t1,'Email Hosting','service',5.99,2.00,now()-interval '75 days'),
(pr7,t1,'CDN Service','service',19.99,8.00,now()-interval '75 days'),
(pr8,t1,'Database Backup','service',14.99,6.00,now()-interval '70 days'),
(pr9,t1,'DDoS Protection','service',24.99,10.00,now()-interval '70 days'),
(pr10,t1,'Monitoring Suite','service',34.99,12.00,now()-interval '65 days')
ON CONFLICT DO NOTHING;

-- PRODUCT VARIANTS (10)
INSERT INTO product_variants (id,tenant_id,product_id,attribute,value,extra_price,created_at) VALUES
(gen_random_uuid(),t1,pr1,'Region','US-East',0),
(gen_random_uuid(),t1,pr1,'Region','EU-West',5.00),
(gen_random_uuid(),t1,pr1,'Region','Asia-Pacific',8.00),
(gen_random_uuid(),t1,pr2,'Storage','100GB',0),
(gen_random_uuid(),t1,pr2,'Storage','500GB',20.00),
(gen_random_uuid(),t1,pr2,'Storage','1TB',45.00),
(gen_random_uuid(),t1,pr3,'SLA','99.9%',0),
(gen_random_uuid(),t1,pr3,'SLA','99.99%',50.00),
(gen_random_uuid(),t1,pr7,'Bandwidth','1TB',0),
(gen_random_uuid(),t1,pr7,'Bandwidth','10TB',15.00)
ON CONFLICT DO NOTHING;

-- TAXES (10)
INSERT INTO taxes (id,tenant_id,name,rate,type,created_at) VALUES
(tx1,t1,'GST 18%',18.00,'percentage'),
(tx2,t1,'GST 12%',12.00,'percentage'),
(tx3,t1,'GST 5%',5.00,'percentage'),
(tx4,t1,'VAT 20%',20.00,'percentage'),
(tx5,t1,'VAT 10%',10.00,'percentage'),
(gen_random_uuid(),t1,'Sales Tax 8.5%',8.50,'percentage'),
(gen_random_uuid(),t1,'Service Tax 15%',15.00,'percentage'),
(gen_random_uuid(),t1,'Eco-Tax 2%',2.00,'percentage'),
(gen_random_uuid(),t1,'Luxury Tax 25%',25.00,'percentage'),
(gen_random_uuid(),t1,'Import Duty 7%',7.00,'percentage')
ON CONFLICT DO NOTHING;

-- DISCOUNTS (10)
INSERT INTO discounts (id,tenant_id,name,type,value,min_purchase,min_qty,start_date,end_date,usage_limit,used_count,applies_to,created_at) VALUES
(dc1,t1,'Welcome 10%','percent',10,0,1,current_date-30,current_date+90,100,5,'subscription'),
(dc2,t1,'Loyalty 15%','percent',15,50,1,current_date-60,current_date+120,50,12,'subscription'),
(dc3,t1,'Flat $5 Off','fixed',5,20,1,current_date-10,current_date+60,200,30,'product'),
(dc4,t1,'Bulk Buy 20%','percent',20,100,5,current_date-20,current_date+45,30,3,'product'),
(dc5,t1,'Early Bird 25%','percent',25,0,1,current_date,current_date+30,20,0,'subscription'),
(dc6,t1,'Flash Sale $10','fixed',10,30,1,current_date,current_date+7,500,150,'product'),
(dc7,t1,'VIP 30%','percent',30,200,1,current_date-90,current_date+365,10,2,'subscription'),
(dc8,t1,'Referral $15','fixed',15,0,1,current_date-5,current_date+60,100,20,'subscription'),
(dc9,t1,'Startup 50%','percent',50,0,1,current_date,current_date+90,15,1,'subscription'),
(dc10,t1,'Seasonal 12%','percent',12,0,1,current_date-15,current_date+45,NULL,45,'product')
ON CONFLICT DO NOTHING;

-- PLANS (10)
INSERT INTO plans (id,tenant_id,name,price,billing_period,min_qty,start_date,end_date,features_json,flags_json,created_at) VALUES
(pl1,t1,'Starter Monthly',29.99,'monthly',1,current_date-90,NULL,'{"support":"email","api":false}','{"auto_close":false,"closable":true,"pausable":false,"renewable":true}',now()-interval '85 days'),
(pl2,t1,'Starter Yearly',299.99,'yearly',1,current_date-90,NULL,'{"support":"email","api":false}','{"auto_close":false,"closable":true,"pausable":false,"renewable":true}',now()-interval '85 days'),
(pl3,t1,'Professional Monthly',79.99,'monthly',1,current_date-90,NULL,'{"support":"priority","api":true}','{"auto_close":false,"closable":true,"pausable":true,"renewable":true}',now()-interval '80 days'),
(pl4,t1,'Professional Yearly',799.99,'yearly',1,current_date-90,NULL,'{"support":"priority","api":true}','{"auto_close":false,"closable":true,"pausable":true,"renewable":true}',now()-interval '80 days'),
(pl5,t1,'Enterprise Monthly',199.99,'monthly',1,current_date-90,NULL,'{"support":"dedicated","api":true,"custom_domain":true}','{"auto_close":false,"closable":true,"pausable":true,"renewable":true}',now()-interval '75 days'),
(pl6,t1,'Enterprise Yearly',1999.99,'yearly',1,current_date-90,NULL,'{"support":"dedicated","api":true,"custom_domain":true}','{"auto_close":false,"closable":true,"pausable":true,"renewable":true}',now()-interval '75 days'),
(pl7,t1,'Team Monthly',149.99,'monthly',5,current_date-90,NULL,'{"support":"priority","api":true,"seats":10}','{"auto_close":false,"closable":true,"pausable":true,"renewable":true}',now()-interval '70 days'),
(pl8,t1,'Team Yearly',1499.99,'yearly',5,current_date-90,NULL,'{"support":"priority","api":true,"seats":10}','{"auto_close":false,"closable":true,"pausable":true,"renewable":true}',now()-interval '70 days'),
(pl9,t1,'Basic Weekly',9.99,'weekly',1,current_date-90,NULL,'{"support":"email","api":false}','{"auto_close":true,"closable":true,"pausable":false,"renewable":true}',now()-interval '60 days'),
(pl10,t1,'Premium Daily',4.99,'daily',1,current_date-90,NULL,'{"support":"email","api":false}','{"auto_close":true,"closable":true,"pausable":false,"renewable":true}',now()-interval '60 days')
ON CONFLICT DO NOTHING;

-- SUBSCRIPTIONS (10)
INSERT INTO subscriptions (id,tenant_id,number,customer_id,plan_id,start_date,expiry_date,payment_terms,status,discount_id,created_at) VALUES
(s1,t1,'SUB-001',p1,pl1,current_date-60,current_date+305,'net-30','active',dc1,now()-interval '60 days'),
(s2,t1,'SUB-002',p1,pl3,current_date-30,current_date+335,'net-30','active',dc2,now()-interval '30 days'),
(s3,t1,'SUB-003',p2,pl5,current_date-90,current_date+275,'net-30','active',NULL,now()-interval '90 days'),
(s4,t1,'SUB-004',p2,pl2,current_date-5,current_date+360,'net-30','confirmed',NULL,now()-interval '5 days'),
(s5,t1,'SUB-005',p3,pl7,current_date-45,current_date+320,'net-30','active',dc5,now()-interval '45 days'),
(s6,t1,'SUB-006',p3,pl4,current_date-120,current_date+245,'net-30','paused',NULL,now()-interval '120 days'),
(s7,t1,'SUB-007',p4,pl6,current_date-20,current_date+345,'net-30','active',dc7,now()-interval '20 days'),
(s8,t1,'SUB-008',p4,pl1,current_date-200,current_date-20,'net-30','closed',NULL,now()-interval '200 days'),
(s9,t1,'SUB-009',p1,pl9,current_date,current_date+7,'net-15','draft',NULL),
(s10,t1,'SUB-010',p2,pl8,current_date-15,current_date+350,'net-30','active',dc9,now()-interval '15 days')
ON CONFLICT DO NOTHING;

-- SUBSCRIPTION LINES (10)
INSERT INTO subscription_lines (id,tenant_id,subscription_id,product_id,qty,unit_price,tax_ids,created_at) VALUES
(gen_random_uuid(),t1,s1,pr1,1,29.99,ARRAY[tx1]::uuid[]),
(gen_random_uuid(),t1,s2,pr2,2,79.99,NULL),
(gen_random_uuid(),t1,s3,pr3,1,199.99,ARRAY[tx1]::uuid[]),
(gen_random_uuid(),t1,s4,pr4,3,9.99,NULL),
(gen_random_uuid(),t1,s5,pr5,5,12.99,ARRAY[tx2]::uuid[]),
(gen_random_uuid(),t1,s6,pr6,2,5.99,NULL),
(gen_random_uuid(),t1,s7,pr7,1,19.99,ARRAY[tx1]::uuid[]),
(gen_random_uuid(),t1,s8,pr8,1,14.99,NULL),
(gen_random_uuid(),t1,s9,pr9,1,24.99,ARRAY[tx3]::uuid[]),
(gen_random_uuid(),t1,s10,pr10,3,34.99,NULL)
ON CONFLICT DO NOTHING;

-- INVOICES (10)
INSERT INTO invoices (id,tenant_id,invoice_number,subscription_id,customer_id,status,due_date,subtotal,tax_total,discount_total,total,amount_paid,created_at) VALUES
(i1,t1,'INV-2026-001',s1,p1,'paid',current_date-20,29.99,5.40,0,35.39,35.39,now()-interval '50 days'),
(i2,t1,'INV-2026-002',s1,p1,'paid',current_date+10,29.99,5.40,3.00,32.39,32.39,now()-interval '20 days'),
(i3,t1,'INV-2026-003',s2,p1,'confirmed',current_date+20,79.99,14.40,0,94.39,0,now()-interval '10 days'),
(i4,t1,'INV-2026-004',s3,p2,'overdue',current_date-10,199.99,36.00,0,235.99,0,now()-interval '40 days'),
(i5,t1,'INV-2026-005',s3,p2,'draft',current_date+30,199.99,36.00,0,235.99,0),
(i6,t1,'INV-2026-006',s5,p3,'paid',current_date,149.99,27.00,0,176.99,176.99,now()-interval '30 days'),
(i7,t1,'INV-2026-007',s7,p4,'confirmed',current_date+15,1999.99,360.00,0,2359.99,0,now()-interval '15 days'),
(i8,t1,'INV-2026-008',s8,p4,'cancelled',current_date-150,29.99,5.40,0,35.39,0,now()-interval '180 days'),
(i9,t1,'INV-2026-009',s10,p2,'paid',current_date+20,1499.99,270.00,0,1769.99,1769.99,now()-interval '10 days'),
(i10,t1,'INV-2026-010',s4,p2,'draft',current_date+30,299.99,54.00,0,353.99,0)
ON CONFLICT DO NOTHING;

-- INVOICE LINES (10)
INSERT INTO invoice_lines (id,tenant_id,invoice_id,product_id,qty,unit_price,tax_id,discount_id,created_at) VALUES
(gen_random_uuid(),t1,i1,pr1,1,29.99,tx1,NULL),
(gen_random_uuid(),t1,i2,pr1,1,29.99,tx1,dc1),
(gen_random_uuid(),t1,i3,pr2,2,79.99,NULL,NULL),
(gen_random_uuid(),t1,i4,pr3,1,199.99,tx1,NULL),
(gen_random_uuid(),t1,i5,pr3,1,199.99,tx2,NULL),
(gen_random_uuid(),t1,i6,pr5,5,12.99,NULL,dc3),
(gen_random_uuid(),t1,i7,pr7,1,19.99,tx1,NULL),
(gen_random_uuid(),t1,i8,pr8,1,14.99,NULL,NULL),
(gen_random_uuid(),t1,i9,pr10,3,34.99,tx1,NULL),
(gen_random_uuid(),t1,i10,pr4,3,9.99,NULL,dc6)
ON CONFLICT DO NOTHING;

-- PAYMENTS (10)
INSERT INTO payments (id,tenant_id,invoice_id,customer_id,method,amount,paid_at,created_at) VALUES
(gen_random_uuid(),t1,i1,p1,'card',35.39,now()-interval '25 days'),
(gen_random_uuid(),t1,i2,p1,'bank',32.39,now()-interval '15 days'),
(gen_random_uuid(),t1,i6,p3,'paypal',176.99,now()-interval '5 days'),
(gen_random_uuid(),t1,i9,p2,'card',1769.99,now()-interval '2 days'),
(gen_random_uuid(),t1,i1,p1,'card',10.00,now()-interval '20 days'),
(gen_random_uuid(),t1,i2,p1,'cash',5.00,now()-interval '12 days'),
(gen_random_uuid(),t1,i6,p3,'bank',50.00,now()-interval '3 days'),
(gen_random_uuid(),t1,i9,p2,'paypal',100.00,now()-interval '1 day'),
(gen_random_uuid(),t1,i1,p1,'other',15.00,now()-interval '18 days'),
(gen_random_uuid(),t1,i6,p3,'card',25.00,now()-interval '4 days')
ON CONFLICT DO NOTHING;

-- SESSIONS (10)
INSERT INTO sessions (id,user_id,tenant_id,refresh_token_hash,family_id,device_fingerprint,ip_subnet,expires_at,revoked_at,created_at) VALUES
(ss1,sa,NULL,md5('token1'),gen_random_uuid(),'chrome-win',  '192.168.1.0/24',now()+interval '7 days',NULL),
(ss2,c1,t1, md5('token2'),gen_random_uuid(),'chrome-mac',  '192.168.1.10/24',now()+interval '7 days',NULL),
(ss3,c2,t2, md5('token3'),gen_random_uuid(),'firefox-linux','10.0.0.0/24',now()+interval '7 days',NULL),
(ss4,c3,t3, md5('token4'),gen_random_uuid(),'safari-ios',  '172.16.0.0/24',now()+interval '7 days',NULL),
(ss5,p1,t1, md5('token5'),gen_random_uuid(),'chrome-win',  '192.168.2.0/24',now()+interval '7 days',NULL),
(gen_random_uuid(),p2,t1,md5('token6'),gen_random_uuid(),'edge-win','192.168.3.0/24',now()+interval '7 days',NULL),
(gen_random_uuid(),p3,t1,md5('token7'),gen_random_uuid(),'chrome-android','10.0.1.0/24',now()+interval '7 days',NULL),
(gen_random_uuid(),p5,t2,md5('token8'),gen_random_uuid(),'firefox-win','172.16.1.0/24',now()+interval '7 days',NULL),
(gen_random_uuid(),p6,t2,md5('token9'),gen_random_uuid(),'chrome-mac','192.168.4.0/24',now()-interval '1 day',now()-interval '1 day'),
(gen_random_uuid(),p8,t3,md5('token10'),gen_random_uuid(),'safari-mac','10.0.2.0/24',now()-interval '2 days',now()-interval '2 days')
ON CONFLICT DO NOTHING;

-- AUDIT LOG (10)
INSERT INTO audit_log (id,tenant_id,actor_id,actor_role,entity_type,entity_id,action,diff_json,session_id,created_at) VALUES
(gen_random_uuid(),t1,c1,'company','subscription',s1,'create','{}',ss2,now()-interval '60 days'),
(gen_random_uuid(),t1,c1,'company','subscription',s2,'create','{}',ss2,now()-interval '30 days'),
(gen_random_uuid(),t1,c1,'company','subscription',s3,'status_change','{"field":"status","old":"draft","new":"active"}',ss2,now()-interval '89 days'),
(gen_random_uuid(),t1,c1,'company','plan',pl1,'update','{"field":"price","old":"24.99","new":"29.99"}',ss2,now()-interval '50 days'),
(gen_random_uuid(),t1,c1,'company','invoice',i1,'create','{}',ss2,now()-interval '50 days'),
(gen_random_uuid(),t1,c1,'company','invoice',i4,'status_change','{"field":"status","old":"confirmed","new":"overdue"}',ss2,now()-interval '10 days'),
(gen_random_uuid(),t1,c1,'company','product',pr1,'create','{}',ss2,now()-interval '85 days'),
(gen_random_uuid(),t1,c1,'company','product',pr2,'update','{"field":"sales_price","old":"69.99","new":"79.99"}',ss2,now()-interval '40 days'),
(gen_random_uuid(),t1,c1,'company','discount',dc1,'create','{}',ss2,now()-interval '30 days'),
(gen_random_uuid(),t1,c1,'company','subscription',s7,'create','{}',ss2,now()-interval '20 days')
ON CONFLICT DO NOTHING;

-- DUNNING SCHEDULES (10)
INSERT INTO dunning_schedules (id,tenant_id,invoice_id,attempt_number,action,channel,scheduled_at,status,result_json,created_at) VALUES
(gen_random_uuid(),t1,i4,1,'retry','email',now()-interval '9 days','pending','{}'),
(gen_random_uuid(),t1,i4,2,'retry','email',now()-interval '6 days','pending','{}'),
(gen_random_uuid(),t1,i4,3,'retry','sms',now()-interval '3 days','pending','{}'),
(gen_random_uuid(),t1,i3,1,'retry','email',now()-interval '8 days','success','{"message":"Payment received"}'),
(gen_random_uuid(),t1,i3,2,'retry','sms',now()-interval '5 days','success','{"message":"Reminder acknowledged"}'),
(gen_random_uuid(),t1,i7,1,'retry','email',now()-interval '7 days','success','{"message":"Will pay soon"}'),
(gen_random_uuid(),t1,i7,2,'retry','email',now()-interval '4 days','pending','{}'),
(gen_random_uuid(),t1,i4,4,'suspend','email',now()-interval '1 day','failed','{"error":"No response"}'),
(gen_random_uuid(),t1,i3,3,'cancel','sms',now(),'failed','{"error":"Cancelled by admin"}'),
(gen_random_uuid(),t1,i7,3,'retry','email',now()+interval '2 days','pending','{}')
ON CONFLICT DO NOTHING;

-- CHURN SCORES (10)
INSERT INTO churn_scores (id,tenant_id,customer_id,score,signals_json,computed_at,created_at) VALUES
(gen_random_uuid(),t1,p1,15,'{"days_login":5,"tickets":0,"usage_drop":7,"pay_fail":0}',now()),
(gen_random_uuid(),t1,p2,72,'{"days_login":45,"tickets":3,"usage_drop":35,"pay_fail":1}',now()),
(gen_random_uuid(),t1,p3,45,'{"days_login":20,"tickets":1,"usage_drop":22,"pay_fail":0}',now()),
(gen_random_uuid(),t1,p4,88,'{"days_login":60,"tickets":5,"usage_drop":50,"pay_fail":2}',now()),
(gen_random_uuid(),t2,p5,30,'{"days_login":12,"tickets":1,"usage_drop":15,"pay_fail":0}',now()),
(gen_random_uuid(),t2,p6,60,'{"days_login":30,"tickets":2,"usage_drop":30,"pay_fail":1}',now()),
(gen_random_uuid(),t2,p7,92,'{"days_login":70,"tickets":4,"usage_drop":48,"pay_fail":3}',now()),
(gen_random_uuid(),t3,p8,55,'{"days_login":25,"tickets":2,"usage_drop":27,"pay_fail":0}',now()),
(gen_random_uuid(),t1,p1,20,'{"days_login":8,"tickets":0,"usage_drop":10,"pay_fail":0}',now()-interval '7 days'),
(gen_random_uuid(),t1,p2,78,'{"days_login":50,"tickets":4,"usage_drop":40,"pay_fail":1}',now()-interval '7 days')
ON CONFLICT DO NOTHING;

-- REVENUE RECOGNITION (10)
INSERT INTO revenue_recognition (id,tenant_id,invoice_id,recognized_amount,recognition_date,period,created_at) VALUES
(gen_random_uuid(),t1,i1,2.50,'2026-01-01','2026-01'),
(gen_random_uuid(),t1,i1,2.50,'2026-02-01','2026-02'),
(gen_random_uuid(),t1,i2,2.50,'2026-03-01','2026-03'),
(gen_random_uuid(),t1,i3,6.67,'2026-01-01','2026-01'),
(gen_random_uuid(),t1,i4,16.67,'2026-02-01','2026-02'),
(gen_random_uuid(),t1,i6,12.50,'2026-03-01','2026-03'),
(gen_random_uuid(),t1,i7,166.67,'2026-01-01','2026-01'),
(gen_random_uuid(),t1,i9,125.00,'2026-02-01','2026-02'),
(gen_random_uuid(),t1,i9,125.00,'2026-03-01','2026-03'),
(gen_random_uuid(),t1,i9,125.00,'2026-04-01','2026-04')
ON CONFLICT DO NOTHING;

-- QUOTATION TEMPLATES (10)
INSERT INTO quotation_templates (id,tenant_id,name,validity_days,plan_id,created_at) VALUES
(gen_random_uuid(),t1,'Starter Proposal',30,pl1),
(gen_random_uuid(),t1,'Professional Pitch',15,pl3),
(gen_random_uuid(),t1,'Enterprise Offer',45,pl5),
(gen_random_uuid(),t1,'Annual Starter Deal',60,pl2),
(gen_random_uuid(),t1,'Annual Pro Deal',60,pl4),
(gen_random_uuid(),t1,'Team Package',30,pl7),
(gen_random_uuid(),t1,'Enterprise Annual',90,pl6),
(gen_random_uuid(),t1,'Quick Trial',7,pl9),
(gen_random_uuid(),t1,'Premium Daily Plan',3,pl10),
(gen_random_uuid(),t1,'Team Annual Bundle',45,pl8)
ON CONFLICT DO NOTHING;

END;
$$;

COMMIT;
