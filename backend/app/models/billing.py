"""SQLAlchemy models — Billing & Payments"""
import uuid
from datetime import datetime
import enum
from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class BillStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    CLOSED = "CLOSED"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    UPI = "UPI"
    CARD = "CARD"


class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    table_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tables.id"), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("table_sessions.id"), nullable=False)
    bill_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    cgst_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    sgst_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    service_charge: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    round_off: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    status: Mapped[BillStatus] = mapped_column(Enum(BillStatus), default=BillStatus.UNPAID)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="bill")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bills.id"), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.SUCCESS)
    upi_vpa: Mapped[str | None] = mapped_column(Text, nullable=True)
    upi_reference_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_link_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_by_staff_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("staff_users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bill: Mapped["Bill"] = relationship("Bill", back_populates="payments")
