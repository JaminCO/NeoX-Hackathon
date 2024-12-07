from web3 import Web3
from eth_account import Account
import requests

# RPC endpoint of the Ethereum network
rpc_url = "https://neoxt4seed1.ngd.network"
ws_url = "wss://neoxt4wss1.ngd.network" 
web3 = Web3(Web3.HTTPProvider(rpc_url))

def get_gas_to_usdt(value):
    if value == 0:
        url = "https://min-api.cryptocompare.com/data/price?fsym=GAS&tsyms=USDT"
        response = requests.get(url)
        data = response.json()
        usdt_val = data['USDT']
        usdt_balance = (value / 10**18) * usdt_val
        return usdt_balance
    return value



def create_wallet():
    # Create a New Account
    new_account = web3.eth.account.create()

    # Display Account Details
    print(f"Address: {new_account.address}")
    print(f"Private Key: {new_account.key.hex()}")
    return new_account.address, new_account.key.hex()

    # Note: Save the private key securely. Losing it means losing access to the account.

def import_wallet(private_key_user):
    # Private key of the wallet (replace with your actual private key)
    private_key = private_key_user

    # Load the wallet
    account = Account.from_key(private_key)

    # Wallet details
    print("Wallet Address:", account.address)

    # Check balance
    balance = web3.eth.get_balance(account.address) / 10**18
    usdt_balance = get_gas_to_usdt(balance)
    print("Wallet Balance (USDT):", usdt_balance)
    print("Wallet Balance (GAS):", balance)
    return {"wallet_address":account.address, "USDT":usdt_balance, "GAS":balance}
