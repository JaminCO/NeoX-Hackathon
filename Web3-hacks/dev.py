from web3 import Web3
import json
import asyncio
from web3 import AsyncWeb3
from web3.providers.persistent import (
    AsyncIPCProvider,
    WebSocketProvider,
)
import requests

# # Wallet or contract address to monitor
wallet_address = "0x38A8E09dE82A13fd31Fbe5D19E52BfF46A94f1c9" 
rpc_url = "https://neoxt4seed1.ngd.network"


# Connect to an Ethereum node (e.g., using Infura or a local node)
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Set up the addresses you're interested in
address_1 = '0x38A8E09dE82A13fd31Fbe5D19E52BfF46A94f1c9'  # Replace with the first address
address_2 = '0xa80CDa9D4898E2Cb232453ded54Fcb56b03e01Ae'  # Replace with the second address

# Create a filter for pending transactions (unmined)


# Function to fetch ETH to USDT price from CoinGecko
def get_gas_to_usdt(value):
    url = "https://min-api.cryptocompare.com/data/price?fsym=GAS&tsyms=USDT"
    response = requests.get(url)
    data = response.json()
    usdt_val = data['USDT']
    usdt_balance = (value / 10**18) * usdt_val
    return usdt_balance

# Poll for new pending transactions
def monitor_confirmed_transactions(tx_hash):
    t_hash = f"0x{tx_hash.hex()}"
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if receipt:
            print(f"Transaction {t_hash} mined in block {receipt['blockNumber']}")
            return receipt  # Return receipt if mined
    except Exception as e:
        print(f"Transaction {t_hash} not mined yet or invalid: {e}")
    return None



# Function to check if a transaction meets the criteria
def check_transaction(tx_hash, address_1, address_2, target_amount):
    try:
        # Get the transaction details using the transaction hash
        tx = w3.eth.get_transaction(tx_hash)

        if tx:
            t_hash = f"0x{tx['hash'].hex()}"
            vals = tx['value'] / 10**18
            # Check if the transaction is between the two addresses and the amount is correct
            if (tx['from'].lower() == address_1.lower() and tx['to'].lower() == address_2.lower()) or \
                (tx['from'].lower() == address_2.lower() and tx['to'].lower() == address_1.lower()):
                if vals == target_amount:
                    print(f"Transaction found: {t_hash}")
                    print(f"From: {tx['from']}")
                    print(f"To: {tx['to']}")
                    print(f"Amount: {tx['value'] / 10**18} GAS")
                    print(f"Amount: {get_gas_to_usdt(tx['value'])} USDT")
                    return True
    except Exception as e:
        print(f"Error fetching transaction {tx_hash}: {e}")
    return False

# Poll for new pending transactions
def monitor_pending_transactions():
    filter = w3.eth.filter('pending')
    print("Starting...")
    datas = True
    while datas:
        # Get all new pending transactions
        pending_transactions = w3.eth.get_filter_changes(filter.filter_id)
        
        # Loop through each pending transaction and check if it meets the criteria
        for tx_hash in pending_transactions:
            t_hash = f"0x{tx_hash.hex()}"
            data = check_transaction(tx_hash, address_1, address_2, target_amount=0.35)
            if data:
                print(f"Transaction {t_hash} matches criteria. Waiting for confirmation...")

            # Wait for transaction to be mined
            receipt = None
            while not receipt:
                receipt = monitor_confirmed_transactions(tx_hash)

            # Confirm successful mining
            if receipt['status'] == 1:
                print(f"Transaction {t_hash} successfully mined and confirmed.")
                datas = False
                break
            else:
                print(f"Transaction {t_hash} failed.")
            datas = False
            break
        if not datas:
            break

# Start monitoring
monitor_pending_transactions()
