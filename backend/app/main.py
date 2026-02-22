"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
import app.models  # ensure all models are registered before create_all

from app.routers import auth, restaurant, menu, cart, orders, billing, webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are already created via migrations/seeding
    yield


app = FastAPI(
    title="HelloDine API",
    description="WhatsApp QR-based dine-in ordering system for Indian restaurants",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(restaurant.router)
app.include_router(menu.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(billing.router)
app.include_router(webhook.router)


@app.get("/")
async def root():
    return {"service": "HelloDine API", "status": "running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
