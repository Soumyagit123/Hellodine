# Hellodine — WhatsApp QR Dine-In Ordering System (India Production-Ready Spec v2)

## Scope
- ✅ Dine-in only (QR per table)
- ❌ No delivery
- ❌ No pickup
- ✅ Order sent to kitchen immediately after customer CONFIRM
- ✅ Pay at end (cashier) with optional UPI deep link at table
- ✅ WhatsApp Interactive Messages (lists + buttons)
- ✅ India-ready menu tags (Veg/Non-Veg/Jain/Spice/Allergens)
- ✅ GST-compliant billing (CGST/SGST split)
- 🔜 Multi-language ready (EN/HIN now; Odia Phase 2)
- ❗No WhatsApp “template system” is included in this spec (intentionally excluded for now)

---

# 1) End-to-End Workflow

## 1.1 Setup (Admin)

### A) Restaurant, Branches, Tables
1) Create Restaurant (Brand)
2) Create Branches (Patia, KIIT…)
3) Create Tables (T1…T30 per branch)

### B) Connect WhatsApp (Cloud API) — Brand-Level Number
- One WhatsApp Business number per restaurant brand is connected to Hellodine backend.
- Incoming webhook provides `phone_number_id`.
- System maps: `phone_number_id → restaurant_id`.

### C) Secure QR per Table
QR prefilled message:

HELLODINE_START
branch=<BRANCH_CODE or BRANCH_ID>
table=<TABLE_NUMBER>
token=<SECURE_RANDOM_TOKEN>

- Backend validates token and locks a session to branch + table.

### D) Menu Setup (India-Ready)
Menu supports:
- categories, items, variants, modifiers
- is_veg (🟢/🔴), is_jain
- spice_level
- allergens
- HSN code
- GST slab (restricted)

---

# 2) Customer Journey (WhatsApp UX with Interactive Messages)

## Step 1 — QR Pairing
Customer scans QR and sends message.

Backend:
- validate token
- create/attach `table_session`
- lock: restaurant_id, branch_id, table_id, customer_id

Bot replies using interactive buttons:
- Veg / Non-Veg / Beverages / Specials

## Step 2 — Browse Menu (List Messages)
Use WhatsApp list message for:
- categories
- item selection
This reduces text errors.

## Step 3 — Add to Cart
Customer taps item or types:
- “Add 1 paneer tikka”

Bot uses buttons for:
- variant selection
- required modifiers

Cart summary includes:
- item lines
- modifiers
- notes
- running total

## Step 4 — Modify Cart Anytime
Supports:
- add/remove
- quantity changes
- notes (e.g., “less spicy”)
- modifiers updates

## Step 5 — Place Order (Immediate Kitchen Dispatch)
Customer presses **CONFIRM** button.

System:
- runs `checkout_guard` validations
- creates order(s)
- status = NEW
- pushes to kitchen instantly
- payment remains UNPAID

Bot:
> “✅ Order sent to kitchen. You can add more items anytime. Payment at billing time.”

---

# 3) Kitchen Workflow (PWA)
Columns:
- NEW → ACCEPTED → PREPARING → READY → SERVED

Each order card:
- Table number (big)
- Order number
- Items + modifiers + notes (highlight)
- Time elapsed
- Status action buttons

Realtime updates:
- status change triggers WhatsApp update to the customer

---

# 4) Add-on Orders During Meal
New items mid-meal:
- create child order with `parent_order_id`
- send as separate kitchen ticket
- avoids editing already-preparing ticket

---

# 5) Billing & Payment (India Dine-In Model)

## Step 1 — Customer Requests Bill
Customer: “Bill please”

System:
- aggregates all OPEN orders for that table/session
- generates consolidated bill (UNPAID)
- sends bill summary in WhatsApp

## Step 2 — Payment at End
Customer pays:
- Cash / UPI / Card

Cashier dashboard:
- open table bill
- “Mark as Paid”
- method + amount + reference (optional)
System:
- creates payment record
- sets bill = PAID
- closes session
- sends receipt via WhatsApp

## Optional Upgrade — UPI Deep Link at Table
- Bot sends payment link/QR
- Customer pays from seat
- Cashier verifies and confirms receipt
- Receipt sent after confirmation

---

# 6) Table Isolation & Security
1) QR token validation
2) session locking (server-side)
3) orders always tied to branch_id + table_id
4) branch-scoped staff access prevents cross-branch leakage

---

# 7) Database Schema (Corrected & Complete)

## 7.1 Core Tenancy

### restaurants
- id (uuid PK)
- name (text)
- gstin (text, nullable)  — brand-level GSTIN (optional if branch GSTIN differs)
- fssai_license_number (text, nullable)
- whatsapp_phone_number_id (text, unique)  — Cloud API phone_number_id mapping
- whatsapp_display_number (text)
- created_at (timestamptz)

### branches
- id (uuid PK)
- restaurant_id (uuid FK → restaurants.id)
- name (text)
- address (text)
- city (text)
- state (text)
- pincode (text)
- gstin (text, nullable) — branch GSTIN for multi-state expansion
- created_at (timestamptz)

### tables
- id (uuid PK)
- branch_id (uuid FK → branches.id)
- table_number (int)
- is_active (bool)
- created_at (timestamptz)
UNIQUE(branch_id, table_number)

### table_qr_tokens
- id (uuid PK)
- table_id (uuid FK → tables.id)
- token (text unique)
- is_revoked (bool)
- valid_from (timestamptz)
- valid_to (timestamptz, nullable)
- created_at (timestamptz)

---

## 7.2 Auth / Staff (Required)

### staff_users
- id (uuid PK)
- restaurant_id (uuid FK → restaurants.id)
- branch_id (uuid FK → branches.id, nullable)  — null = all branches
- role (enum: SUPER_ADMIN / BRANCH_ADMIN / KITCHEN / CASHIER)
- name (text)
- phone (text unique)
- password_hash (text)
- is_active (bool)
- created_at (timestamptz)

---

## 7.3 Customers & Sessions

### customers
- id (uuid PK)
- restaurant_id (uuid FK → restaurants.id)
- wa_user_id (text) — WhatsApp user id
- preferred_language (enum: en/hi/or, default en)
- name (text, nullable)
- created_at (timestamptz)
UNIQUE(restaurant_id, wa_user_id)

### table_sessions
- id (uuid PK)
- restaurant_id (uuid FK → restaurants.id)
- branch_id (uuid FK → branches.id)
- table_id (uuid FK → tables.id)
- customer_id (uuid FK → customers.id)
- status (enum: ACTIVE / CLOSED)
- started_at (timestamptz)
- last_message_at (timestamptz)
- closed_at (timestamptz, nullable)
- auto_closed_at (timestamptz, nullable)

---

## 7.4 Menu (India-Ready)

### menu_categories
- id (uuid PK)
- branch_id (uuid FK → branches.id)
- name (text)
- sort_order (int)
- estimated_prep_minutes (int, nullable)
- is_active (bool)

### menu_items
- id (uuid PK)
- branch_id (uuid FK → branches.id)
- category_id (uuid FK → menu_categories.id)
- name (text)
- description (text, nullable)
- base_price (numeric(10,2))
- gst_percent (int) — constrain to allowed slabs
- hsn_code (text, nullable)
- is_veg (bool)
- is_jain (bool)
- spice_level (enum: mild / medium / hot, nullable)
- allergens (text[], nullable)
- calories (int, nullable)
- is_available (bool)
- created_at (timestamptz)
- updated_at (timestamptz)

**Constraint:** gst_percent IN (0, 5, 12, 18)

### menu_item_variants
- id (uuid PK)
- menu_item_id (uuid FK → menu_items.id)
- name (text)
- price (numeric(10,2))
- is_available (bool)

### menu_modifier_groups
- id (uuid PK)
- menu_item_id (uuid FK → menu_items.id)
- name (text)
- min_select (int)
- max_select (int)
- is_required (bool)

### menu_modifiers
- id (uuid PK)
- modifier_group_id (uuid FK → menu_modifier_groups.id)
- name (text)
- price_delta (numeric(10,2))
- is_available (bool)

---

## 7.5 Cart

### carts
- id (uuid PK)
- session_id (uuid FK → table_sessions.id)
- status (enum: OPEN / CHECKED_OUT)
- subtotal (numeric(10,2))
- cgst_amount (numeric(10,2))
- sgst_amount (numeric(10,2))
- service_charge (numeric(10,2), default 0)
- discount (numeric(10,2), default 0)
- round_off (numeric(10,2), default 0)
- total (numeric(10,2))
- updated_at (timestamptz)

> NOTE (India compliance): service_charge must be OPTIONAL and only added with explicit customer consent. Default 0.

### cart_items
- id (uuid PK)
- cart_id (uuid FK → carts.id)
- menu_item_id (uuid FK → menu_items.id)
- variant_id (uuid FK → menu_item_variants.id, nullable)
- quantity (int)
- unit_price (numeric(10,2))
- notes (text, nullable)
- line_total (numeric(10,2))

### cart_item_modifiers  ✅ (Fix: required)
- id (uuid PK)
- cart_item_id (uuid FK → cart_items.id)
- modifier_id (uuid FK → menu_modifiers.id)
- modifier_name_snapshot (text)      — snapshot at time of selection
- price_delta_snapshot (numeric(10,2))

---

## 7.6 Orders (with Idempotency)

### orders
- id (uuid PK)
- branch_id (uuid FK → branches.id)
- table_id (uuid FK → tables.id)
- session_id (uuid FK → table_sessions.id)
- order_number (text)
- parent_order_id (uuid FK → orders.id, nullable)
- cart_hash (text) ✅ idempotency key
- status (enum: NEW / ACCEPTED / PREPARING / READY / SERVED / CANCELLED)
- subtotal (numeric(10,2))
- cgst_amount (numeric(10,2))
- sgst_amount (numeric(10,2))
- total (numeric(10,2))
- created_at (timestamptz)
- updated_at (timestamptz)

### order_items
- id (uuid PK)
- order_id (uuid FK → orders.id)
- menu_item_id (uuid FK → menu_items.id)
- variant_id (uuid FK → menu_item_variants.id, nullable)
- quantity (int)
- unit_price (numeric(10,2))
- hsn_code_snapshot (text, nullable)
- notes (text, nullable)
- line_total (numeric(10,2))

### order_item_modifiers
- id (uuid PK)
- order_item_id (uuid FK → order_items.id)
- modifier_id (uuid FK → menu_modifiers.id)
- modifier_name_snapshot (text)
- price_delta_snapshot (numeric(10,2))

---

## 7.7 Billing & Payments

### bills
- id (uuid PK)
- branch_id (uuid FK → branches.id)
- table_id (uuid FK → tables.id)
- session_id (uuid FK → table_sessions.id)
- bill_number (text)
- subtotal (numeric(10,2))
- cgst_amount (numeric(10,2))
- sgst_amount (numeric(10,2))
- service_charge (numeric(10,2), default 0)
- discount (numeric(10,2), default 0)
- round_off (numeric(10,2), default 0)
- total (numeric(10,2))
- status (enum: UNPAID / PAID / CLOSED)
- created_at (timestamptz)
- closed_at (timestamptz, nullable)

> NOTE: service_charge must be opt-in, not auto-applied.

### payments
- id (uuid PK)
- bill_id (uuid FK → bills.id)
- method (enum: CASH / UPI / CARD)
- amount (numeric(10,2))
- status (enum: SUCCESS)
- upi_vpa (text, nullable)
- upi_reference_id (text, nullable)
- payment_link_url (text, nullable)
- received_by_staff_user_id (uuid FK → staff_users.id, nullable)
- created_at (timestamptz)

---

## 7.8 WhatsApp Logging (Strongly Recommended)

### whatsapp_message_logs ✅ (Fix: recommended)
- id (uuid PK)
- restaurant_id (uuid FK → restaurants.id)
- wa_message_id (text, unique)   — dedupe protection
- session_id (uuid FK → table_sessions.id, nullable)
- direction (enum: INBOUND / OUTBOUND)
- message_type (text)            — text / interactive
- raw_payload (jsonb)
- delivery_status (enum: SENT / DELIVERED / READ / FAILED, nullable)
- created_at (timestamptz)

---

# 8) LangGraph Workflow (Corrected)

## 8.1 State
- restaurant_id
- branch_id
- table_id
- session_id
- customer_id
- preferred_language
- intent
- cart_snapshot
- pending_clarification
- final_response

## 8.2 Nodes
1) ingest_webhook
2) resolve_session
3) detect_language
4) intent_router
5) menu_retrieval
6) action_planner
7) cart_executor
8) checkout_guard ✅ (defined below)
9) kitchen_dispatch
10) bill_generator
11) receipt_sender
12) response_formatter (interactive message builder)

## 8.3 checkout_guard (Definition)
Before creating an order, validate:
1) cart is not empty
2) session is ACTIVE
3) all items still available
4) required modifiers/variants satisfied
5) idempotency: compute `cart_hash` and reject if same hash created an order within last 30 seconds

**cart_hash recommendation:**
- hash(session_id + normalized_cart_items + timestamp_bucket_30s)

---

# 9) Kitchen Dashboard MVP (Auth Included)

## Roles
- SUPER_ADMIN / BRANCH_ADMIN
- KITCHEN
- CASHIER

## Screens
1) Login (phone + password/PIN)
2) Orders board (realtime status columns)
3) Order detail view
4) Billing view (cashier):
   - generate bill
   - mark paid
   - method + reference
5) Admin:
   - menu management
   - tables
   - staff management
   - basic daily report

---

# MVP Must-Haves (Final)
- QR pairing with secure token
- WhatsApp interactive lists/buttons
- Cart + modifiers storage
- checkout_guard idempotency protections
- Realtime kitchen PWA with staff auth
- GST split billing (CGST/SGST)
- Pay-at-end cashier marking + receipt
- WhatsApp message logging with dedupe key

END OF SPEC v2 (No template-message subsystem included)

