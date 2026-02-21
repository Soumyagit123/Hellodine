"""SQLAlchemy models — Cart"""
import uuid
from datetime import datetime
import enum
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CartStatus(str, enum.Enum):
    OPEN = "OPEN"
    CHECKED_OUT = "CHECKED_OUT"


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("table_sessions.id"), nullable=False)
    status: Mapped[CartStatus] = mapped_column(Enum(CartStatus), default=CartStatus.OPEN)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    cgst_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    sgst_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    service_charge: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    round_off: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    session: Mapped["TableSession"] = relationship("TableSession", back_populates="cart")  # type: ignore
    items: Mapped[list["CartItem"]] = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("carts.id"), nullable=False)
    menu_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("menu_items.id"), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("menu_item_variants.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    modifiers: Mapped[list["CartItemModifier"]] = relationship("CartItemModifier", back_populates="cart_item", cascade="all, delete-orphan")


class CartItemModifier(Base):
    __tablename__ = "cart_item_modifiers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cart_items.id"), nullable=False)
    modifier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("menu_modifiers.id"), nullable=False)
    modifier_name_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    price_delta_snapshot: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    cart_item: Mapped["CartItem"] = relationship("CartItem", back_populates="modifiers")
