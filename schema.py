from pydantic import BaseModel

class WalletImportRequest(BaseModel):
    private_key: str

class InitiatePaymentRequest(BaseModel):
    amount: float
    data: str
    sender_address: str
    webhook: str

class BusinessBase(BaseModel):
    user_id: str
    email: str
    business_name: str
    api_key: str
    created_at: str
    updated_at: str

class CreateBusiness(BaseModel):
    email: str
    business_name: str
    password: str

class LoginBusiness(BaseModel):
    email: str
    password: str

# class PaymentBase(BaseModel):
#     payment_id
#     user_id
#     receiver_address
#     amount
#     sender_address
#     status
#     transaction_hash 
#     created_at
#     updated_at


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: str | None = None
    sub: str = None
    exp: int = None

class UserInDB(BaseModel):
    user_id: str
    email: str
    business_name: str
    password_hash: str

class BusinessOut(BusinessBase):
    password: str

class CreateCheckoutRequest(BaseModel):
    amount: float

class InitiateCheckout(BaseModel):
    payment_id: str
    data: str
    sender_address: str

class WithdrawRequest(BaseModel):
    amount: float
    receiver_address: str
