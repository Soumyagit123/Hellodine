Got it: ONLY dine-in, and QR → WhatsApp → table-by-table ordering, end-to-end.

Below is the complete workflow in “real restaurant steps” + what your system is doing behind the scenes at each step. (I’ll keep it practical, not theoretical.)

0) What Hellodine is in this version

Every restaurant (and each branch) has its own WhatsApp number connected to your Hellodine backend via WhatsApp Business Platform (Cloud API) webhooks.

Every table has a QR code that starts a WhatsApp chat and “pairs” the customer to Branch + Table.

No delivery. No pickup. Only table ordering.

1) Setup inside the restaurant (before customers)
1.1 Branch and table creation

Restaurant admin dashboard:

Create Branch (Patia / KIIT / etc.)

Define Tables (T1…T30)

Create / upload Menu (items, variants, add-ons, allergens, availability)

1.2 WhatsApp linking (branch/restaurant number)

This is the “connect my WhatsApp to Hellodine” step:

Restaurant logs into your dashboard → clicks Connect WhatsApp

Uses Meta’s onboarding (“Embedded Signup”) to connect their WhatsApp Business number to your platform

After this, all messages sent to that number reach your server via webhooks

1.3 QR code printing per table

For each table, you generate a QR that opens WhatsApp with a pre-filled pairing message.

Example prefilled message (internal format):

HELLODINE_START
branch=PATIA
table=7
token=AbC123


You print and stick that QR on the table.

Why token?

Prevents people from typing “table=7” from outside and messing with orders.

Token is unique per table (and can be rotated).

2) Customer journey: end-to-end dine-in flow
Step 1 — Customer sits at Table 7 and scans QR

Customer action

Scans QR → WhatsApp opens chat with restaurant number

That prefilled message is ready → customer taps Send

System action

Your webhook receives the message.

You validate:

token is valid for Branch=Patia, Table=7

token not expired / not already locked incorrectly

Create a Table Session:

branch_id=patia

table_id=7

session_id=XYZ

customer_wa_id=+91xxxx

session state = ORDERING

Bot reply (example)
“Hi! I’m Hellodine 😊 You’re at Patia – Table 7.
Would you like to see Veg, Non-veg, Beverages, or Today’s specials?”

Step 2 — Customer explores menu (in WhatsApp)

Customer

“Show veg starters”

or “Something spicy”

or “Paneer items”

System

Menu retrieval (RAG/search over menu + tags like spicy/veg/jain)

Respond with “menu cards” style messages:

Item name, price, short description

Ask quantity / variant if needed

Bot example
“Here are Veg Starters:

Paneer Tikka ₹220

Gobi Manchurian ₹190

Crispy Corn ₹200
Reply: add 1 paneer tikka or details 2”

Step 3 — Customer orders by chatting (cart gets built)

Customer
“Add 2 paneer tikka and 1 lime soda”

System

Intent: ADD_ITEMS

Deterministic cart engine:

checks item exists

checks availability

applies quantity

Saves cart in DB for session_id XYZ

Bot
“Done ✅ Added:

Paneer Tikka ×2

Lime Soda ×1
Anything else? You can say show main course or checkout.”

Step 4 — Customer changes order anytime (your key use-case)

Customer
“Make paneer tikka one spicy, and remove lime soda”

System

Intent: MODIFY_CART

“One spicy” triggers modifier selection:

Paneer Tikka has spice modifier?

If not, add a note field (kitchen note)

Remove lime soda

Updates cart state

Bot
“Updated ✅

Paneer Tikka ×2 (1 spicy note added)

Lime Soda removed
Current total: ₹___
Anything else?”

This can happen anytime until kitchen acceptance rules you define.

3) Checkout: “Place Order” to kitchen (KDS)
Step 5 — Customer says “Place order”

Customer
“Place order”

System

Bot shows final confirmation (must do this to reduce mistakes):

items, modifiers, notes

table number

Customer confirms: “confirm”

Bot
“Please confirm Table 7 order:
Paneer Tikka ×2 (1 spicy)
Total ₹___
Reply CONFIRM or EDIT”

Customer
“CONFIRM”

4) Kitchen workflow: chef sees Table 7
Step 6 — Order appears on Kitchen Screen

System

Creates Order ID (e.g., PAT-000381)

Status = NEW

Push realtime event to kitchen dashboard:

“Table 7 → New order”

Kitchen dashboard shows:

Table 7, Order ID

Items, modifiers, notes

Buttons: Accept, Preparing, Ready, Served

Chef

Taps Accept

System

Status changes to ACCEPTED

WhatsApp message to customer:
“✅ Order accepted! Estimated prep time: 12–15 minutes.”

5) After confirmation: “Entertainment mode” (safe version)
Step 7 — Bot offers engagement while food prepares

Bot
“While your food is being prepared, want a joke, trivia, short video links, or music suggestions?”

(Important: avoid “sing any song lyrics” due to copyright risk—use links or original content.)

Step 8 — Customer can still add items mid-meal

Customer
“Add 2 butter naan”

System
Two rules you can choose:

Rule A (recommended): Add-on creates a new order ticket

Create a new child order: PAT-000382 linked to Table 7

Kitchen sees it separately (clear and standard)

Rule B: Append to same order

Only allowed until status PREPARING; after that it becomes messy.

Bot
“Added ✅ Butter Naan ×2. Sending to kitchen now.”

Kitchen gets the add-on ticket instantly.

6) Table-by-table isolation (how you guarantee it)

You’ll enforce isolation at 3 layers:

QR token pairing

Only valid tokens can start a table session.

Server-side session lock

Every incoming WhatsApp message maps to:

customer_wa_id + active_session_id

That session is already locked to Branch+Table.

Kitchen permissions

Kitchen UI is per-branch login.

They only see orders for their branch.

So Table 7’s customer chat can never affect Table 9 unless you explicitly allow “merge table” features.

7) Multiple branches: how it works cleanly

You have 2 clean models:

Model 1: One WhatsApp number per branch (simplest ops)

Patia has its own number

KIIT has its own number

Each QR points to that branch’s number

✅ Super simple routing
❌ More phone numbers to manage

Model 2: One WhatsApp number for whole brand (more scalable)

One number for “Hellodine Restaurant”

QR message includes branch_id and token

System routes internally

✅ Fewer numbers
✅ Easy brand marketing
❌ Requires perfect routing logic (still doable)

8) WhatsApp “24-hour window” (operational detail you must know)

WhatsApp allows free-form replies within a 24-hour customer service window after the user’s last message; outside that window you typically need pre-approved templates.

For dine-in, it’s usually fine because customers message frequently.
But for “feedback request next day”, you’ll use templates.

9) Where n8n fits (fast, but scalable)

For your dine-in use-case:

Use n8n for non-critical automation

Send owner daily report

Push “Order Ready” to a TV display

Log to Google Sheets

Trigger WhatsApp template messages (feedback request)
n8n is great for glue automation.

Don’t use n8n as the core ordering brain

Core ordering needs:

strict cart state

idempotency (avoid duplicate orders)

realtime kitchen events

table locking

Scalable pattern
WhatsApp webhook → your backend (state + cart + DB) → emits events → n8n handles extras.

That keeps it scalable for “huge customers”.

10) End-to-end “Happy Path” summary (one glance)

Restaurant connects WhatsApp number (Cloud API)

Admin creates branches + tables + menu

QR printed per table (with secure token)

Customer scans → WhatsApp chat opens → session locked to Table

Customer chats → cart updates live

Customer confirms → order goes to kitchen screen

Kitchen updates status → WhatsApp updates customer

Customer can add more items anytime (new add-on ticket)

Optional engagement while waiting