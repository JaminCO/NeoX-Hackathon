from sqlalchemy import Column, String, Integer, DECIMAL, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base
import secrets

class Business(Base):
    __tablename__ = "businesses"

    user_id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    business_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


    # website = db.Column(db.String(200))
    # integration_type = db.Column(db.String(50))
    # monthly_volume = db.Column(db.String(50))
    # business_type = db.Column(db.String(50))
    # country = db.Column(db.String(50))

    wallets = relationship("Wallet", back_populates="owner")
    payments = relationship("Payment", back_populates="business")
    analytics = relationship("Analytics", back_populates="business")


class Wallet(Base):
    __tablename__ = "wallets"

    wallet_id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("businesses.user_id"), nullable=False)
    address = Column(String, unique=True, nullable=False)
    private_key = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    owner = relationship("Business", back_populates="wallets")


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("businesses.user_id"), nullable=False)
    receiver_address = Column(String, nullable=False)
    data = Column(String, nullable=True)
    amount = Column(DECIMAL(18, 8), nullable=False)
    sender_address = Column(String, nullable=True)
    status = Column(String, default="Pending")
    transaction_hash = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("Business", back_populates="payments")
    transactions = relationship("Transaction", back_populates="payment")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    payment_id = Column(String, ForeignKey("payments.payment_id"), nullable=False)
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

    analytics_id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("businesses.user_id"), nullable=False)
    total_payments = Column(Integer, default=0)
    total_revenue = Column(DECIMAL(18, 8), default=0)
    last_updated = Column(TIMESTAMP, default=datetime.utcnow)

    business = relationship("Business", back_populates="analytics")
