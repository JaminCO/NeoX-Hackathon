from fastapi import FastAPI, Depends, HTTPException, WebSocket, BackgroundTasks, statu, APIRouter
import requests
import asyncio

from sqlalchemy.orm import Session
import uuid
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta

from xenon import create_wallet, import_wallet, get_gas_to_usdt
from schema import WalletImportRequest, InitiatePaymentRequest, CreateBusiness, Token, TokenData, UserInDB, LoginBusiness, BusinessOut, CreateCheckoutRequest, InitiateCheckout
from database import SessionLocal, engine, get_db
from models import Base, Business, Wallet, Payment, Transaction, Analytics
import monitor

router = APIRouter()


# # JWT Configuration
SECRET_KEY = "your_secret_key"  # Use a secure, random secret key


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Create tables
Base.metadata.create_all(bind=engine)

async def transacts(data, db):
    sender_address = data["sender"]
    reciever_address = data["recv"]
    amount = data["amount"]
    email = data["email"]
    payment_id = data["payment_id"]
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()

    result = monitor.monitor_transactions(sender_address, reciever_address, amount)
    if result != False:
        payment.transaction_hash = result["tx_hash"]
        payment.status = "Successful"
        db.commit()
        db.refresh(payment)

# Utility Functions
def to_dict(model):
    """Convert SQLAlchemy model instance to dictionary."""
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}

def send_webhook(data, url):
    response = requests.post(url, data=data)
    print(response.json())
    return response.json()

# Dependency
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user = db.query(Business).filter(Business.api_key == token).first()
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user

# Routes
@router.get("/")
def read_root():
    return {"message": "Welcome to NeoX Crypto Payment Gateway!"}

@router.post("/payment/create", response_model=dict, tags=["Payment"])
def initiate_payment(body: InitiatePaymentRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to initiate payment to business.
    """
    business_wallet = db.query(Wallet).filter(Wallet.user_id == body.business_id).first()
    if not business_wallet:
        raise HTTPException(status_code=404, detail="No wallet related to business")
    reciever_address = business_wallet.address
    
    amount = body.amount
    
    sender_address = body.sender_address
    payment = Payment(user_id=body.business_id, data=body.data, receiver_address=reciever_address, amount=amount, sender_address=sender_address)
    db.add(payment)
    db.commit()
    db.refresh(payment)

    post_data = {
        "sender": sender_address,
        "recv": reciever_address,
        "amount": amount,
        "email": body.data,
        "payment_id": payment.payment_id
    }
    background_tasks.add_task(transacts, post_data, db)
    return {"payment_id": payment.payment_id, "merchant_address":reciever_address}

@router.post("/me", tags=["Business"])
async def business_details(db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    data = {}
    wallets = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
    payments = db.query(Payment).filter(Payment.user_id == business.user_id).all()
    if wallets == None:
        transactions = []
    else:
        transactions = db.query(Transaction).filter(Transaction.to_address == wallets.address).all()
    analytics = db.query(Analytics).filter(Analytics.user_id == business.user_id).all()
    data["business"] = business
    data["wallets"] = wallets
    data["payment"] = payments
    data["transaction"] = transactions
    data["analytics"] = analytics
    return data

@router.get("/get/{paymentId}", response_model=dict, tags=["Payment"])
def get_payment(paymentId: str, db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to get Payment Id details.
    """
    payment = db.query(Payment).filter(Payment.payment_id == paymentId).first()
    if not payment:
        raise HTTPException(status_code=404, detail="No Payment with this ID")
    
    amount = payment.amount
    total_amount = get_gas_to_usdt(amount)

    post_data = {
        "payment_id": payment.payment_id,
        "business_name": payment.business.business_name,
        "business_id": payment.user_id,
        "gas_amount": amount,
        "total_amount": total_amount,
    }
    return post_data