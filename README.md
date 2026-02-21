# HelloDine 🍽️

HelloDine is a WhatsApp QR-based dine-in ordering system designed for Indian restaurants. It replaces physical menus with an AI-powered conversational WhatsApp bot and provides a real-time Kitchen & Cashier PWA.

## 🚀 Architecture
- **Backend**: FastAPI (Python 3.12), PostgreSQL (asyncpg), Redis (WebSockets)
- **AI Bot**: LangGraph, Google Gemini 2.5 Flash (`langchain-google-genai`)
- **Frontend**: React 18, Vite, TypeScript, Custom CSS Design System
- **Deployment**: Docker Compose

## 🛠️ Quick Start

### 1. Environment Setup
Fill out your `.env` file (copied from `.env.example`).
Make sure to add your **Gemini API Key** and **WhatsApp Cloud API** credentials if you intend to use the WhatsApp bot live.
```bash
GEMINI_API_KEY=your_gemini_key_here
```

### 2. Start Services
Run the entire stack using Docker Compose:
```bash
docker-compose up --build
```
This will start:
- `postgres` (Port 5432)
- `redis` (Port 6379)
- `backend` (FastAPI at http://localhost:8000)
- `frontend` (React PWA at http://localhost:5173)

### 3. Seed Demo Data
Once the backend is healthy, open a new terminal and run the seed script to create a demo restaurant, branch, tables, staff, and a full menu.
```bash
docker-compose exec backend python seed.py
```

### 4. Access the Kitchen PWA
Open your browser and navigate to:
**http://localhost:5173**

Log in using the seeded credentials:
- **Cashier/Admin** - Phone: `+91 9000000003` | PIN: `cashier123`
- **Super Admin** - Phone: `+91 9000000001` | PIN: `admin123`

## 📱 Simulating WhatsApp Orders Locally
Since WhatsApp webhooks require a public URL (like Ngrok), you can simulate bot interactions locally by sending a POST request to the webhook endpoint.

```bash
curl -X POST http://localhost:8000/api/webhook \
-H "Content-Type: application/json" \
-d '{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "YOUR_PHONE_NUMBER_ID",
    "changes": [{
      "value": {
        "metadata": {
          "display_phone_number": "1234567890",
          "phone_number_id": "YOUR_PHONE_NUMBER_ID"
        },
        "messages": [{
          "from": "919876543210",
          "id": "wamid.simulated.123",
          "type": "text",
          "text": { "body": "HELLODINE_START_valid_token_here" }
        }]
      }
    }]
  }]
}'
```
*(Note: Replace `YOUR_PHONE_NUMBER_ID` with the ID in your DB or wait for the real webhook setup via Ngrok).*

## 🌟 Features Implemented
- **AI Intent Router (Gemini)**: Fast NL classification for Browse, Add Item, Modify Cart, and Checkout.
- **GST Billing**: Automatic split of CGST (4.5%) and SGST (4.5%) ensuring compliance.
- **Idempotency**: Prevent duplicate order placements using a `cart_hash`.
- **Kanban Board**: Real-time kitchen dashboard connected via WebSockets.
- **QR Token Auth**: Secure, time-bound session initiation preventing remote abuse.
- **PWA Ready**: Installable app for kitchen tablets with custom icons and manifest.
