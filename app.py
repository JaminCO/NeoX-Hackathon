from fastapi import FastAPI, Depends, HTTPException, WebSocket, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
import requests
import asyncio

from sqlalchemy.orm import Session
import uuid
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta

from xenon import create_wallet, import_wallet
from schema import WalletImportRequest, InitiatePaymentRequest, CreateBusiness, Token, TokenData, UserInDB, LoginBusiness, BusinessOut
from database import SessionLocal, engine, get_db
from models import Base, Business, Wallet, Payment, Transaction, Analytics
import monitor


app = FastAPI(title="Crypto Wallet API")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # JWT Configuration
SECRET_KEY = "your_secret_key"  # Use a secure, random secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Create tables
Base.metadata.create_all(bind=engine)
active_connections = {}

async def transacts(data, db):
    sender_address = data["sender"]
    reciever_address = data["recv"]
    amount = data["amount"]
    email = data["email"]
    payment_id = data["payment_id"]
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    print("Payment Data Found")

    result = monitor.monitor_transactions(sender_address, reciever_address, amount)
    if result != False:
        print(result,"DONE")
        payment.transaction_hash = result["tx_hash"]
        payment.status = "Successful"
        db.commit()
        db.refresh(payment)
        if email in active_connections:
            websocket = active_connections[email]
            await websocket.send_json(payment.status)


# Utility Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, email: str):
    user = db.query(Business).filter(Business.email == email).first()
    if user:
        return UserInDB(**user)
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
    return {"message": "Welcome to the Crypto Wallet API!"}


@app.post("/users/signup", tags=["Auth"])
def create_user(body: CreateBusiness, db: Session = Depends(get_db)):
    user = db.query(Business).filter(Business.email == body.email).first()
    if user is not None:
        raise HTTPException(
            status_code=450,
            detail="Business with this email already exists"
        )
    hashed_password = get_password_hash(body.password)
    user = Business(email=body.email, business_name=body.business_name, password_hash=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user_id": user.user_id}

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

@app.post('/token', summary="Create access and refresh tokens for user", response_model=Token, tags=["Auth"])
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
    address, private_key = create_wallet()
    wallet = Wallet(user_id=business.user_id, address=address, private_key=private_key)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    wallet = {
        "wallet_address": address,
        "private_key": private_key
    }
    return {"message": "Wallet created successfully", "wallet": wallet, "wallet_id":wallet.wallet_id}

@app.post("/wallet/import", response_model=dict, tags=["Wallet"])
def import_existing_wallet(body: WalletImportRequest, db: Session = Depends(get_db)):
    """
    API endpoint to import an existing wallet using a private key.
    """
    try:
        wallet = import_wallet(body.private_key)
        return {"message": "Wallet imported successfully", "wallet": wallet}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payment/create", response_model=dict)
def initiate_payment(body: InitiatePaymentRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    """
    API endpoint to initiate payment to business.
    """
    business_wallet = db.query(Wallet).filter(Wallet.user_id == body.business_id).first()
    print(business_wallet)
    if not business_wallet:
        raise HTTPException(status_code=404, detail="No wallet related to business")
    reciever_address = business_wallet.address
    
    amount = body.amount
    
    sender_address = body.sender_address
    payment = Payment(user_id=body.business_id, data=body.data, receiver_address=reciever_address, amount=amount, sender_address=sender_address)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    print("Payment Created in DB")

    post_data = {
        "sender": sender_address,
        "recv": reciever_address,
        "amount": amount,
        "email": body.data,
        "payment_id": payment.payment_id
    }
    background_tasks.add_task(transacts, post_data, db)
    return {"payment_id": payment.payment_id, "merchant_address":reciever_address}

@app.post("/me")
async def business_details(db: Session = Depends(get_db), business: BusinessOut = Depends(get_current_user)):
    data = {}
    wallets = db.query(Wallet).filter(Wallet.user_id == business.user_id).first()
    payments = db.query(Payment).filter(Payment.user_id == business.user_id).all()
    transactions = db.query(Transaction).filter(Transaction.to_address == wallets.address).all()
    analytics = db.query(Analytics).filter(Analytics.user_id == business.user_id).all()
    data["business"] = business
    data["wallets"] = wallets
    data["payment"] = payments
    data["transaction"] = transactions
    data["analytics"] = analytics
    return data

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    active_connections[user_id] = websocket  # Store the connection
    try:
        while True:
            # Keep the connection open
            await asyncio.sleep(200)
    except Exception as e:
        print(f"WebSocket connection closed for {user_id}: {e}")
    finally:
        active_connections.pop(user_id, None)  # Remove connection on disconnect


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True)