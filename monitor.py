from web3 import Web3
import json
import time
import asyncio
from web3 import AsyncWeb3
from web3.providers.persistent import (
    AsyncIPCProvider,
    WebSocketProvider,
)
import requests

# # Wallet or contract address to monitor
rpc_url = "https://neoxt4seed1.ngd.network"


# Connect to an Ethereum node (e.g., using Infura or a local node)
w3 = Web3(Web3.HTTPProvider(rpc_url))


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
        pass
        # print(f"Transaction {t_hash} not mined yet or invalid: {e}")
    return None



# Function to check if a transaction meets the criteria
def check_transaction(tx_hash, sender_address, receiver_address, target_amount):
    try:
        # Get the transaction details using the transaction hash
        tx = w3.eth.get_transaction(tx_hash)

        if tx:
            t_hash = f"0x{tx['hash'].hex()}"
            vals = tx['value'] / 10**18

            # Check if the transaction is between the two addresses and the amount is correct
            if (tx['from'].lower() == sender_address.lower() and tx['to'].lower() == receiver_address.lower()):
                if vals == target_amount:
                    print(f"Transaction found: {t_hash}")
                    print(f"From: {tx['from']}")
                    print(f"To: {tx['to']}")
                    print(f"Amount: {tx['value'] / 10**18} GAS")
                    print(f"Amount: {get_gas_to_usdt(tx['value'])} USDT \n")
                    return tx
    except Exception as e:
        print(f"Error fetching transaction {tx_hash}: {e}")
    return False

# Poll for new pending transactions
def monitor_transactions(address_1, address_2, target_amount):
    filter = w3.eth.filter('pending')
    print("Starting...")
    
    datas = True
    while datas:
        # Get all new pending transactions
        pending_transactions = w3.eth.get_filter_changes(filter.filter_id)
        
        # Loop through each pending transaction and check if it meets the criteria
        for tx_hash in pending_transactions:
            t_hash = f"0x{tx_hash.hex()}"
            data = check_transaction(tx_hash, address_1, address_2, target_amount)
            if data:
                print(f"Transaction {t_hash} matches criteria. Waiting for confirmation...")
                # Wait for transaction to be mined
                receipt = None
                while not receipt:
                    time.sleep(2)
                    receipt = monitor_confirmed_transactions(tx_hash)

                # Confirm successful mining
                if receipt['status'] == 1:
                    print(f"Transaction {t_hash} successfully mined and confirmed.")
                    return {"receipt":receipt, "tx_hash":t_hash}
                    datas = False
                    break
                else:
                    print(f"Transaction {t_hash} failed.")
                    return False
                datas = False
                break
    return False