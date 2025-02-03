from fastapi import FastAPI, Depends, HTTPException, WebSocket, BackgroundTasks, status, APIRouter
import requests
import asyncio

from sqlalchemy.orm import Session
import uuid
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta

from xenon import create_wallet, import_wallet, get_gas_to_usdc
from schema import WalletImportRequest, InitiatePaymentRequest, CreateBusiness, Token, TokenData, UserInDB, LoginBusiness, BusinessOut, CreateCheckoutRequest, InitiateCheckout
from database import SessionLocal, engine, get_db
from models import Base, Business, Wallet, Payment, Transaction, Analytics
import monitor
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError


# Initialize ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=5)


router = APIRouter()


# # JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Create tables
Base.metadata.create_all(bind=engine)

FRONTEND_URL = os.getenv("FRONTEND_URL")

def transacts(data, db):
    url = data["webhook"]
    sender_address = data["sender"]
    reciever_address = data["recv"]
    amount = data["amount"]
    email = data["email"]
    payment_id = data["payment_id"]
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()

    result = monitor.monitor_transactions(sender_address, reciever_address, amount)
    print('hereeeeee')
    if result != False:
        # Prepare transaction data
        print("DATAAA")
        receipt = result["receipt"]
        gas_used = receipt['gasUsed']
        gas_price = receipt['effectiveGasPrice']
        gas_fee = (gas_used * gas_price) / 10**18  # Convert from Wei to native token
        print(gas_fee)

        transaction_data = {
            "transaction_hash": result["tx_hash"],
            "status": 1,  # 1 for successful
            "receipt": receipt,
            "amount": amount,
            "gas_fee": gas_fee,
            "blockNumber": receipt['blockNumber']
        }

        # Update payment and create transaction
        update_payment_and_create_transaction(payment_id, transaction_data, db)

        # Prepare webhook data
        webhook_data = {
            "receipt": result,
            "email": email,
            "payment_id": payment_id,
            "status": "Successful",
            "amount": amount,
            "sender": sender_address,
            "receiver": reciever_address,
            "transaction_hash": result["tx_hash"],
            "user_id": payment.user_id,
            "gas_fee": gas_fee
        }

        response = requests.post(url, json=webhook_data)
        if response.status_code == 200:
            print(response.json())
        else:
            print(f"Failed to send webhook. Status code: {response.status_code}, Response: {response.text}")
        
    else:
        transaction_data = {
            "transaction_hash": "Failed",
            "status": 0,  # 0 for failed
            "receipt": {"from": sender_address, "to": reciever_address},
            "amount": amount,
            "gas_fee": 0,
            "blockNumber": None
        }
        update_payment_and_create_transaction(payment_id, transaction_data, db)

def update_payment_and_create_transaction(payment_id, transaction_data, db: Session = Depends(get_db)):
    """
    Update the payment table and create a new row in the Transactions table.
    Args:
        payment_id: UUID of the payment
        transaction_data: Dict containing:
            - transaction_hash: str
            - status: int (1 for success, 0 for failure)
            - receipt: dict with 'from' and 'to' addresses
            - amount: float
            - gas_fee: float
            - blockNumber: int or None
    """
    # Update the payment table
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="No Payment with this ID")
    
    # Update payment status
    payment.transaction_hash = transaction_data["transaction_hash"]
    payment.status = "Successful" if transaction_data["status"] == 1 else "Failed"
    db.commit()
    db.refresh(payment)
    
    # Create a new row in the Transactions table
    new_transaction = Transaction(
        transaction_id=str(uuid.uuid4()),
        payment_id=payment_id,
        from_address=transaction_data["receipt"]["from"],
        to_address=transaction_data["receipt"]["to"],
        amount=transaction_data["amount"],
        gas_fee=transaction_data["gas_fee"],
        status="Successful" if transaction_data["status"] == 1 else "Failed",
        block_number=transaction_data["blockNumber"],
        transaction_hash=transaction_data["transaction_hash"]
    )
    
    try:
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create transaction record: {str(e)}"
        )
    
    return {
        "message": "Payment and Transaction updated successfully",
        "payment_status": payment.status,
        "transaction_id": new_transaction.transaction_id
    }


# Utility Functions
def to_dict(model):
    """Convert SQLAlchemy model instance to dictionary."""
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}

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

@router.post("/payment/create", response_model=dict)
def initiate_payment(body: InitiatePaymentRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to initiate payment to business.
    """
    business_wallet = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
    if not business_wallet:
        raise HTTPException(status_code=404, detail="No wallet related to business")
    reciever_address = business_wallet.address
    
    amount = body.amount
    
    sender_address = body.sender_address
    payment = Payment(payment_id=str(uuid.uuid4()), user_id=business.user_id, data=body.data, receiver_address=reciever_address, amount=amount, sender_address=sender_address)
    db.add(payment)
    db.commit()
    db.refresh(payment)

    post_data = {
        "sender": sender_address,
        "recv": reciever_address,
        "amount": amount,
        "email": body.data,
        "payment_id": payment.payment_id,
        "webhook": body.webhook
    }
    
    future = executor.submit(transacts, post_data, db)
    print(future)

    return {"payment_id": payment.payment_id, "merchant_address":reciever_address}

@router.get("/payment/{paymentId}", response_model=dict)
def get_payment(paymentId: str, db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to get Payment Id details.
    """
    payment = db.query(Payment).filter(Payment.payment_id == paymentId).first()
    if not payment:
        raise HTTPException(status_code=404, detail="No Payment with this ID")
    if business.user_id != payment.user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to view this payment")

    amount = payment.amount
    total_amount = get_gas_to_usdc(amount)

    post_data = {
        "payment_id": payment.payment_id,
        "business_name": payment.business.business_name,
        "business_id": payment.user_id,
        "eth_amount": amount,
        "total_amount": total_amount,
    }
    return post_data

@router.get("/payment/status/{paymentId}", response_model=dict)
def payment_status(paymentId: str, db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to get Payment Id details.
    """
    payment = db.query(Payment).filter(Payment.payment_id == paymentId).first()
    if not payment:
        raise HTTPException(status_code=404, detail="No Payment with this ID")
    if business.user_id != payment.user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to view this payment")

    post_data = {
        "payment_id": payment.payment_id,
        "status": payment.status,
        "transaction_hash": payment.transaction_hash,
    }

    return post_data

@router.get("/transaction/{transactionId}", response_model=dict)
def transaction_details(transactionId: str, db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to get Transaction Id details.
    """
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transactionId).first()
    business_wallet = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="No Transaction with this ID")
    if business_wallet.address != transaction.to_address:
        raise HTTPException(status_code=403, detail="You are not authorized to view this transaction")

    post_data = to_dict(transaction)

    return post_data

@router.get("/transaction/to/{wallet_address}")
def wallet_transactions(wallet_address: str, db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to get Transactions to a wallet address.
    """
    transactions = db.query(Transaction).filter(Transaction.to_address == wallet_address).all()
    business_wallet = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
    if not transactions:
        raise HTTPException(status_code=404, detail="No Transactions to this wallet address")
    if business_wallet.address != wallet_address:
        raise HTTPException(status_code=403, detail="You are not authorized to view these transactions")

    post_data = [to_dict(transaction) for transaction in transactions]

    return post_data
