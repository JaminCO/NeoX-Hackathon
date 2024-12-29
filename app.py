from fastapi import FastAPI, Depends, HTTPException, WebSocket, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
import requests
import asyncio

from sqlalchemy.orm import Session
import uuid
import os
import secrets
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta

from xenon import create_wallet, import_wallet, get_gas_to_usdt, get_wallet_balances
from schema import WalletImportRequest, CreateBusiness, Token, TokenData, UserInDB, LoginBusiness, BusinessOut, CreateCheckoutRequest, InitiateCheckout
from database import SessionLocal, engine, get_db
from models import Base, Business, Wallet, Payment, Transaction, Analytics
import monitor
import api
from concurrent.futures import ThreadPoolExecutor, TimeoutError


# Initialize ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=5)

app = FastAPI(title="Crypto Wallet API")

app.include_router(api.router, prefix="/api/v1", tags=["API V1"])

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Create tables
Base.metadata.create_all(bind=engine)

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
def generate_api_key():
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)

def to_dict(model):
    """Convert SQLAlchemy model instance to dictionary."""
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, email: str):
    user = db.query(Business).filter(Business.email == email).first()
    if user:
        return UserInDB(**to_dict(user))
    return None

def authenticate_user(db, email: str, password: str):
    user = get_user(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Dependency
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenData(**payload)
        email = token_data.sub
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(Business).filter(Business.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Routes
@app.get("/")
def read_root():
    return {"message": "Welcome to NeoX Crypto Payment Gateway!"}


@app.post("/users/signup", tags=["Auth"])
def create_user(body: CreateBusiness, db: Session = Depends(get_db)):
    user = db.query(Business).filter(Business.email == body.email).first()
    if user is not None:
        raise HTTPException(
            status_code=450,
            detail="Business with this email already exists"
        )
    hashed_password = get_password_hash(body.password)
    api_key = generate_api_key()
    user = Business(
        user_id=str(uuid.uuid4()),
        email=body.email, 
        business_name=body.business_name, 
        password_hash=hashed_password,
        api_key=api_key
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    address, private_key = create_wallet()
    wallet = Wallet(user_id=user.user_id, address=address, private_key=private_key)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return {
        "user_id": user.user_id,
        "api_key": api_key
    }

@app.post("/login", response_model=Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usr = db.query(Business).filter(Business.business_name == form_data.username).first()
    user = authenticate_user(db, usr.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email}, 
                                       expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post('/users/token', summary="Create access and refresh tokens for user", response_model=Token, tags=["Auth"])
async def login_token(data: LoginBusiness, db: Session = Depends(get_db)):
    result = db.query(Business).filter(Business.email == data.email).first()

    user = result
    if user is None:
        raise HTTPException(
            status_code=451,
            detail="Incorrect email or password"
        )

    hashed_pass = user.password_hash
    if not verify_password(data.password, hashed_pass):
        raise HTTPException(
            status_code=451,
            detail="Incorrect email or password"
        )
    
    return {
        "access_token": create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)),
        "token_type": "bearer"
    }


@app.post("/wallet/create", response_model=dict, tags=["Wallet"])
def create_new_wallet(db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to create a new crypto wallet.
    """
    # Check if business already has a wallet
    existing_wallet = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
    if existing_wallet:
        raise HTTPException(
            status_code=400,
            detail="Business already has a wallet"
        )
    address, private_key = create_wallet()
    wallet = Wallet(user_id=business.user_id, address=address, private_key=private_key)
    wallet_id = wallet.wallet_id
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    wallet = {
        "wallet_address": address,
        "private_key": private_key
    }
    return {"message": "Wallet created successfully", "wallet": wallet, "wallet_id":wallet_id}

@app.post("/wallet/import", response_model=dict, tags=["Wallet"])
def import_existing_wallet(body: WalletImportRequest, db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to import an existing wallet using a private key.
    """
    try:
        existing_wallet = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
        if existing_wallet:
            raise HTTPException(
                status_code=400,
                detail="Business already has a wallet"
            )
        wallet = import_wallet(body.private_key)
        wallet = Wallet(user_id=business.user_id, address=wallet["wallet_address"], private_key=body.private_key)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        return {"message": "Wallet imported successfully", "wallet": wallet}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/wallet/balance", response_model=dict, tags=["Wallet"])
def get_wallet_balance(db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to get wallet balances for the business's wallet.
    """
    wallet = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="No wallet found for this business")
        
    balances = get_wallet_balances(wallet.address)
    return {
        "wallet_address": wallet.address,
        "balances": balances
    }


@app.get("/dashboard", tags=["Business"])
async def dashboard_details(db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    data = {}
    wallets = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
    payments = db.query(Payment).filter(Payment.user_id == business.user_id).all()
    if wallets == None:
        return {"message": "Create wallet", "status": 430}
    else:
        transactions = db.query(Transaction).filter(Transaction.to_address == wallets.address).all()
    balances = get_wallet_balances(wallets.address)
    data["balances"] = balances
    data["business"] = business
    data["num_of_payments"] = len(payments)
    data["num_of_transactions"] = len(transactions)
    data["wallets"] = wallets
    data["transactions"] = sorted(payments, key=lambda x: x.created_at, reverse=True)[:3]
    successful_transactions = [t for t in transactions if t.status == "Successful"]
    data["transaction_volume"] = sum(float(t.amount) for t in successful_transactions)
    return data

@app.get("/me", tags=["Business"])
async def business_details(business: BusinessOut = Depends(get_current_user)):
    return business

@app.post("/checkout/create", response_model=dict, tags=["Payment"])
def checkout_create(body: CreateCheckoutRequest, db: Session = Depends(get_db),  business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to initiate payment to business.
    """
    business_wallet = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
    if not business_wallet:
        raise HTTPException(status_code=404, detail="No wallet related to business")
    reciever_address = business_wallet.address
    
    amount = body.amount
    
    payment = Payment(payment_id=str(uuid.uuid4()), user_id=business.user_id, receiver_address=reciever_address, amount=amount)
    db.add(payment)
    db.commit()
    db.refresh(payment)

    url = f"http://127.0.0.1:3000/checkout/{payment.payment_id}"

    post_data = {
        "payment_id": payment.payment_id,
        "url": url
    }
    return post_data

@app.get("/get/{paymentId}", response_model=dict, tags=["Payment"])
def get_payment(paymentId: str, db: Session = Depends(get_db),):
    """
    API endpoint to get Payment Id details.
    """
    payment = db.query(Payment).filter(Payment.payment_id == paymentId).first()
    if not payment:
        raise HTTPException(status_code=404, detail="No Payment with this ID")
    
    amount = payment.amount
    total_amount = get_gas_to_usdt(amount)

    post_data = to_dict(payment)
    post_data["business_name"] = payment.business.business_name
    post_data["business_id"] = payment.user_id
    post_data["gas_amount"] = amount
    post_data["total_amount"] = total_amount
    return post_data

@app.post("/checkout/initiate", response_model=dict, tags=["Payment"])
def initiate_checkout_payment(Data: InitiateCheckout, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    API endpoint to Initiate Checkout Payment.
    """
    payment = db.query(Payment).filter(Payment.payment_id == Data.payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="No Payment with this ID")
    payment.data = Data.data
    payment.sender_address = Data.sender_address
    db.commit()
    db.refresh(payment)

    amount = payment.amount
    total_amount = get_gas_to_usdt(amount)

    post_data = {
        "sender": Data.sender_address,
        "recv": payment.receiver_address,
        "amount": payment.amount,
        "email": Data.data,
        "payment_id": Data.payment_id
    }
    future = executor.submit(transacts, post_data, db)


    data = {
        "payment_id": payment.payment_id,
        "business_name": payment.business.business_name,
        "gas_amount": payment.amount,
        "total_amount": total_amount,
        "merchant_address":payment.receiver_address
    }

    return data

@app.get("/regenerate-api-key", tags=["Business"])
async def regenerate_api_key(db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    Regenerate API key for the authenticated business.
    """
    try:
        # Generate new API key
        new_api_key = generate_api_key()
        
        # Update the business record
        business_record = db.query(Business).filter(Business.user_id == business.user_id).first()
        business_record.api_key = new_api_key
        db.commit()
        db.refresh(business_record)
        
        return {
            "message": "API key regenerated successfully",
            "api_key": new_api_key
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate API key"
        )


@app.get("/transactions/")
@app.get("/transactions/{num}")
def get_transactions(num: str = None, db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to get Transaction to a wallet address.
    """
    wallet = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
    transaction_query = db.query(Transaction).filter(Transaction.to_address == wallet.address)
    
    if num:
        transaction_query = transaction_query.limit(int(num))
    
    transactions = transaction_query.all()
    
    if not transactions:
        pass
        # raise HTTPException(status_code=404, detail="No Transaction to this wallet address")

    post_data = {"transacts":[to_dict(transaction) for transaction in transactions]}

    return post_data

@app.get("/payments/")
@app.get("/payments/{num}")
def get_payments(num: str = None, db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to get Transaction to a wallet address.
    """
    wallet = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
    payment_query = db.query(Payment).filter(Payment.receiver_address == wallet.address)
    
    if num:
        payment_query = payment_query.order_by(Payment.created_at.desc()).limit(int(num))
    
    payments = payment_query.all()
    
    if not payments:
        pass
        # raise HTTPException(status_code=404, detail="No Transaction to this wallet address")
    
    post_data = {"payments":[to_dict(payment) for payment in payments]}

    return post_data
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True)

@app.get("/payment/status/{paymentId}", response_model=dict)
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