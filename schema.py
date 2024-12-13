from pydantic import BaseModel

class WalletImportRequest(BaseModel):
    private_key: str

class InitiatePaymentRequest(BaseModel):
    amount: float
    data: str
    sender_address: str
    receiver_address: str
    business_id: str

class CreateBusiness(BaseModel):
    email: str
    business_name: str
    password: str

class PaymentBase(BaseModel):
    payment_id
    user_id
    receiver_address
    amount
    sender_address
    status
    transaction_hash 
    created_at
    updated_at


class CreatePayment(BaseModel):
    receiver_address: str
    amount: str
    sender_address: str
    status: str
    transaction_hash: str
