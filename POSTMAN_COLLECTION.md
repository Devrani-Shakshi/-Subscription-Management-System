# 🚀 Subscription Management API Collection (FULL PROJECT)

This is the complete API reference for the Subscription Management System. All endpoints are grouped by user roles and tags as they appear in the OpenAPI (Swagger) documentation.

---

## 🔑 Authentication (Public)
*Base URL:* `http://localhost:8000/auth`

### 1. Login
- **Method:** `POST /login`
- **Body:** `{"email": "...", "password": "..."}`
- **Note:** Sets a `refresh_token` HTTP-only cookie.

### 2. Refresh Token
- **Method:** `POST /refresh`
- **Note:** Uses `refresh_token` cookie to issue new access & refresh tokens.

### 3. Logout
- **Method:** `POST /logout`
- **Note:** Revokes current session and clears cookies.

### 4. Bootstrap Super Admin (Seeding)
- **Method:** `POST /seed`
- **Header:** `X-Seed-Secret: <your_secret>`
- **Body:** `{"email": "...", "password": "...", "name": "..."}`

### 5. Accept Invite
- **Method:** `POST /invite/accept`
- **Body:** `{"token": "...", "password": "...", "name": "..."}`

### 6. Self-Registration (Portal)
- **Method:** `POST /register`
- **Body:** `{"email": "...", "password": "...", "name": "...", "tenant_slug": "..."}`

### 7. Revoke All Sessions
- **Method:** `POST /revoke-all`
- **Auth:** Bearer Token

---

## 🏢 Platform Administration (Super Admin Only)
*Base URL:* `http://localhost:8000/admin`
*Required Header:* `Authorization: Bearer <super_admin_token>`

### 1. List All Companies
- **Method:** `GET /companies`
- **Params:** `page`, `page_size`, `status`, `search`

### 2. Create Company & Admin
- **Method:** `POST /companies`
- **Body:** `{"name": "...", "slug": "...", "email": "..."}`

### 3. Check Slug Availability
- **Method:** `GET /companies/check-slug`
- **Param:** `slug`

### 4. Get Company Detail
- **Method:** `GET /companies/{tenant_id}`

### 5. Suspend Company
- **Method:** `PATCH /companies/{tenant_id}/suspend`

### 6. Reactivate Company
- **Method:** `PATCH /companies/{tenant_id}/reactivate`

### 7. Soft-Delete Company
- **Method:** `DELETE /companies/{tenant_id}`

### 8. Platform Dashboard
- **Method:** `GET /dashboard`

### 9. Revenue Analytics
- **Method:** `GET /revenue`
- **Param:** `months` (default 12)

### 10. Global Audit Logs
- **Method:** `GET /audit`
- **Params:** `tenant_id`, `actor_id`, `entity_type`, `action`, `date_from`, `date_to`

### 11. Export Audit Logs (CSV)
- **Method:** `GET /audit/export`

---

## 🏗️ Company Operations (Company Admin Only)
*Base URL:* `http://localhost:8000/company`
*Required Header:* `Authorization: Bearer <company_token>`

### 1. Invite New Customer
- **Method:** `POST /customers/invite`
- **Body:** `{"email": "...", "name": "..."}`

### 2. List Invoices
- **Method:** `GET /invoices`
- **Params:** `offset`, `limit`

### 3. Create Draft Invoice
- **Method:** `POST /invoices`
- **Body:** `{"subscription_id": "..."}`

### 4. Get Invoice Detail
- **Method:** `GET /invoices/{invoice_id}`

### 5. Update Invoice
- **Method:** `PATCH /invoices/{invoice_id}`
- **Body:** `{"due_date": "...", "notes": "..."}`

### 6. Confirm Invoice
- **Method:** `POST /invoices/{invoice_id}/confirm`

### 7. Cancel Invoice
- **Method:** `POST /invoices/{invoice_id}/cancel`

### 8. Send Invoice
- **Method:** `POST /invoices/{invoice_id}/send`

### 9. Download PDF (Internal)
- **Method:** `GET /invoices/{invoice_id}/pdf`

### 10. Bulk Send Invoices
- **Method:** `POST /invoices/bulk-send`
- **Body:** `{"invoice_ids": ["...", "..."]}`

### 11. Record External Payment
- **Method:** `POST /payments`
- **Body:** `{"invoice_id": "...", "amount": "...", "method": "...", "paid_at": "..."}`

### 12. List Payments
- **Method:** `GET /payments`

---

## 👤 Customer Portal (Portal User Only)
*Base URL:* `http://localhost:8000/portal`
*Required Header:* `Authorization: Bearer <portal_user_token>`

### 1. Get My Basic Info
- **Method:** `GET /me`

### 2. Full Profile Detail
- **Method:** `GET /profile`

### 3. Update Profile Name
- **Method:** `PATCH /profile`
- **Body:** `{"name": "..."}`

### 4. Update Billing Address
- **Method:** `PATCH /profile/address`
- **Body:** `{"street": "...", "city": "...", "zip": "...", "country": "..."}`

### 5. Change Password
- **Method:** `POST /profile/change-password`
- **Body:** `{"current_password": "...", "new_password": "..."}`

### 6. My Subscription Dashboard
- **Method:** `GET /my-subscription`

### 7. Preview Plan Change
- **Method:** `GET /my-subscription/change-plan/preview`
- **Param:** `plan_id`

### 8. Execute Plan Change
- **Method:** `POST /my-subscription/change-plan`
- **Body:** `{"plan_id": "..."}`

### 9. Cancel Subscription
- **Method:** `POST /my-subscription/cancel`
- **Body:** `{"reason": "..."}`

### 10. List My Invoices
- **Method:** `GET /invoices`

### 11. Get My Invoice Detail
- **Method:** `GET /invoices/{invoice_id}`

### 12. Download My PDF
- **Method:** `GET /invoices/{invoice_id}/pdf`

### 13. Pay Invoice via Portal
- **Method:** `POST /invoices/{invoice_id}/pay`
- **Body:** `{"method": "card"}`

### 14. Payment History
- **Method:** `GET /payments`

### 15. Active Sessions
- **Method:** `GET /sessions`

### 16. Revoke Specific Session
- **Method:** `DELETE /sessions/{session_id}`

---

## 🌐 Public Discovery (No Auth)
*Base URL:* `http://localhost:8000/public`

### 1. Get Tenant Branding
- **Method:** `GET /tenant/{slug}`

### 2. List Public Plans
- **Method:** `GET /plans?tenant={slug}`
