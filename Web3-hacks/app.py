from fastapi import FastAPI, HTTPException
from xenon import create_wallet, import_wallet
from pydantic import BaseModel


app = FastAPI(title="Crypto Wallet API")

class WalletImportRequest(BaseModel):
    private_key: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Crypto Wallet API!"}

@app.post("/create", response_model=dict)
def create_new_wallet():
    """
    API endpoint to create a new crypto wallet.
    """
    address, private_key = create_wallet()
    wallet = {
        "wallet_address": address,
        "private_key": private_key
    }
    return {"message": "Wallet created successfully", "wallet": wallet}

@app.post("/import", response_model=dict)
def import_existing_wallet(body: WalletImportRequest):
    """
    API endpoint to import an existing wallet using a private key.
    """
    try:
        wallet = import_wallet(body.private_key)
        return {"message": "Wallet imported successfully", "wallet": wallet}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

