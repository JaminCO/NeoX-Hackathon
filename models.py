from sqlalchemy import Column, String, Integer, DECIMAL, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base

class Business(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    business_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    wallets = relationship("Wallet", back_populates="owner")
    payments = relationship("Payment", back_populates="user")
    analytics = relationship("Analytics", back_populates="user")


class Wallet(Base):
    __tablename__ = "wallets"

    wallet_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    address = Column(String, unique=True, nullable=False)
    private_key = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    owner = relationship("User", back_populates="wallets")


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    receiver_address = Column(String, nullable=False)
    amount = Column(DECIMAL(18, 8), nullable=False)
    sender_address = Column(String, nullable=False)
    status = Column(String, default="Pending")
    transaction_hash = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="payments")
    transactions = relationship("Transaction", back_populates="payment")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.payment_id"), nullable=False)
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    amount = Column(DECIMAL(18, 8), nullable=False)
    gas_fee = Column(DECIMAL(18, 8), nullable=False)
    status = Column(String, default="Pending")
    block_number = Column(BigInteger, nullable=True)
    transaction_hash = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    payment = relationship("Payment", back_populates="transactions")


class Analytics(Base):
    __tablename__ = "analytics"

    analytics_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    total_payments = Column(Integer, default=0)
    total_revenue = Column(DECIMAL(18, 8), default=0)
    last_updated = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", back_populates="analytics")
