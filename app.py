from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from xenon import create_wallet, import_wallet
from schema import WalletImportRequest, InitiatePaymentRequest, CreateBusiness
from database import Base, engine, get_db
from models import Business, Wallet, Payment, Transaction, Analytics


app = FastAPI(title="Crypto Wallet API")


# Create tables
Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Crypto Wallet API!"}


@app.post("/users/signup")
def create_user(body: CreateBusiness, db: Session = Depends(get_db)):
    hashed_password = body.password + "hashed"  # Replace with proper hash function
    user = User(email=body.email, business_name=body.business_name, password_hash=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user_id": user.user_id}

@app.post("/wallet/create", response_model=dict)
def create_new_wallet():
    """
    API endpoint to create a new crypto wallet.
    """
    address, private_key = create_wallet()
    wallet = Wallet(user_id=user_id, address=address, private_key=private_key)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    wallet = {
        "wallet_address": address,
        "private_key": private_key
    }
    return {"message": "Wallet created successfully", "wallet": wallet, "wallet_id":wallet.id}

@app.post("/wallet/import", response_model=dict)
def import_existing_wallet(body: WalletImportRequest):
    """
    API endpoint to import an existing wallet using a private key.
    """
    try:
        wallet = import_wallet(body.private_key)
        return {"message": "Wallet imported successfully", "wallet": wallet}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payment/create", response_model=dict)
def initiate_payment(body: InitiatePaymentRequest):
    """
    API endpoint to initiate payment to business.
    """
    business_address = request.receiver_address
    amount = body.amount,
    reciever_address = business_address,
    sender_address = request.sender_address,
    payment = Payment(user_id=user_id, receiver_address=receiver_address, amount=amount, sender_address=sender_address)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return {"payment_id": payment.payment_id, "merchant_address":business_address}

@app.post("/payments/")
def create_payment(user_id: uuid.UUID, receiver_address: str, amount: float, sender_address: str, db: Session = Depends(get_db)):
    
    
    return {"payment_id": payment.payment_id}
