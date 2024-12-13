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


def send_neox_gas(sender_address, private_key, recipient_address, amount_in_ether):
    # Check if connected
    if web3.is_connected():
        print("Connected to Neo X")
    else:
        print("Connection failed")
        return 0

    amount_in_wei = web3.to_wei(amount_in_ether, 'ether')

    # Get the nonce (number of transactions sent from the sender address)
    nonce = web3.eth.get_transaction_count(sender_address)

    # Create the transaction
    tx = {
        'nonce': nonce,
        'to': recipient_address,
        'value': amount_in_wei,
        'gas': 21000,  # Standard gas limit for ETH transfers
        'gasPrice': web3.to_wei('30', 'gwei'),  # Replace '30' with current gas price in Gwei
        'chainId': 12227332  # Mainnet chain ID. Use 3, 4, or 5 for testnets like Ropsten, Rinkeby, or Goerli
    }

    gas_price = web3.eth.gas_price
    tx['gasPrice'] = gas_price

    # Sign the transaction with the sender's private key
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)

    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Get the transaction hash
    print(f"Transaction hash: {web3.to_hex(tx_hash)}")

    # Optional: Wait for the transaction receipt (to confirm it was mined)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction receipt: {receipt}")

    return receipt