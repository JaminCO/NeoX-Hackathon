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
import time


# # Wallet or contract address to monitor
rpc_url = "https://mainnet-1.rpc.banelabs.org"
# "https://neoxt4seed1.ngd.network"


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
            print(f"vals: {vals}")
            print(f"target_amount: {target_amount}")
            print(f"tx['from']: {tx['from']}")
            print(f"sender_address: {sender_address}")
            print(f"tx['to']: {tx['to']}")
            print(f"receiver_address: {receiver_address}")

            # Check if the transaction is between the two addresses and the amount is correct
            if (tx['from'].lower() == sender_address.lower() and tx['to'].lower() == receiver_address.lower()):
                # if vals == target_amount:
                    # print(f"Transaction found: {t_hash}")
                    # print(f"From: {tx['from']}")
                    # print(f"To: {tx['to']}")
                    # print(f"Amount: {tx['value'] / 10**18} GAS")
                    # print(f"Amount: {get_gas_to_usdt(tx['value'])} USDT \n")
                    return tx
    except Exception as e:
        print(f"Error fetching transaction {tx_hash}: {e}")
    return False

# Poll for new pending transactions
def monitor_transactions(address_1, address_2, target_amount, timeout=60*10):
    # with open("transaction_new_log.txt", "a") as file:
        # file.write(f"Monitoring transactions between {address_1} and {address_2} for amount {target_amount} GAS\n")
    start_time = time.time()
    info = False
    filter_id = None
    
    try:
        print("step 1")
        filter = w3.eth.filter('pending')
        filter_id = filter.filter_id

        while (time.time() - start_time) <= timeout:  # Simplified timeout check
            print("step 2")
            pending_transactions = w3.eth.get_filter_changes(filter.filter_id)
            print(f"pending_transactions: {pending_transactions}")
            
            for tx_hash in pending_transactions:
                print("step 3")
                # if (time.time() - start_time) > timeout:
                #     break
                    
                data = check_transaction(tx_hash, address_1, address_2, target_amount)
                print(f"data: {data}")
                if data:
                    print("step 4")
                    receipt = None
                    while not receipt and (time.time() - start_time) <= timeout:
                        time.sleep(2)
                        receipt = monitor_confirmed_transactions(tx_hash)
                        print("step 5")

                    if receipt and receipt['status'] == 1:
                        print("step 6")
                        return {"receipt": receipt, "tx_hash": f"0x{tx_hash.hex()}"}
                    
            # time.sleep(1)   Add small delay to prevent excessive CPU usage
            
        return info
    except:
        if filter_id:
            try:
                w3.eth.uninstall_filter(filter_id)
            except Exception as e:
                print(f"Error uninstalling filter: {e}")
    return info

