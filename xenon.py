from web3 import Web3
from eth_account import Account
import requests

# RPC endpoint of the Ethereum network
rpc_url = "https://neoxt4seed1.ngd.network"
ws_url = "wss://neoxt4wss1.ngd.network" 
web3 = Web3(Web3.HTTPProvider(rpc_url))


def get_gas_to_usdt(value):
    # try:
        if value == 0:
            return 0.0  # Return 0 directly for input value 0
        
        # API Request
        url = "https://min-api.cryptocompare.com/data/price?fsym=GAS&tsyms=USDT"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for HTTP issues
        data = response.json()
        usdt_val = data.get('USDT')  # Safely get 'USDT' value
        if usdt_val is None:
            return "Error: 'USDT' key not found in API response."
        # Calculate equivalent USDT balance
        usdt_balance = float(value) * usdt_val
        # Format the output for readability
        return round(usdt_balance, 6)  # Rounded to 6 decimal places
    # except requests.exceptions.RequestException as e:
    #     return f"API Request Error: {e}"
    # except Exception as e:
    #     return f"An error occurred: {e}"


def create_wallet():
    # Create a New Account
    new_account = web3.eth.account.create()

    # Display Account Details
    # print(f"Address: {new_account.address}")
    # print(f"Private Key: {new_account.key.hex()}")
    return new_account.address, new_account.key.hex()

    # Note: Save the private key securely. Losing it means losing access to the account.

def import_wallet(private_key_user):
    # Private key of the wallet (replace with your actual private key)
    private_key = private_key_user

    # Load the wallet
    account = Account.from_key(private_key)

    # Wallet details
    
    # Check balance
    balance = web3.eth.get_balance(account.address) / 10**18
    usdt_balance = get_gas_to_usdt(balance)
    return {"wallet_address":account.address, "USDT":usdt_balance, "GAS":balance}


def send_neox_gas(sender_address, private_key, recipient_address, amount_in_ether):
    # Check if connected
    if web3.is_connected():
        pass
    else:
        pass
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
    # print(f"Transaction hash: {web3.to_hex(tx_hash)}")

    # Optional: Wait for the transaction receipt (to confirm it was mined)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    # print(f"Transaction receipt: {receipt}")

    return receipt

# from eth_abi import decode
# import json

# # Add this near the top with other constants
# # Example token contract addresses on NeoX (replace with actual addresses)
# TOKEN_CONTRACTS = {
#     "USDT": "0x24222633A8A20A34A7A8eF3ae0Cd3dF2fE36b548",  # Replace with actual USDT contract
#     # Add other tokens as needed
# }

# # Standard ERC20 ABI for token balance checking
# ERC20_ABI = json.loads('''[
#     {
#         "constant": true,
#         "inputs": [{"name": "_owner", "type": "address"}],
#         "name": "balanceOf",
#         "outputs": [{"name": "balance", "type": "uint256"}],
#         "type": "function"
#     },
#     {
#         "constant": true,
#         "inputs": [],
#         "name": "decimals",
#         "outputs": [{"name": "", "type": "uint8"}],
#         "type": "function"
#     }
# ]''')

def get_wallet_balances(wallet_address):
    """
    Get GAS and token balances for a wallet address
    Returns a dictionary with token symbols and their balances
    """
    balances = {}
    
    # Get GAS balance
    gas_balance = web3.eth.get_balance(wallet_address) / 10**18
    balances["GAS"] = gas_balance
    balances["USDT"] = get_gas_to_usdt(gas_balance)
    
    # Get other token balances
    # for token_symbol, contract_address in TOKEN_CONTRACTS.items():
    #     try:
    #         # Create contract instance
    #         contract = web3.eth.contract(address=contract_address, abi=ERC20_ABI)
            
    #         # Get token decimals
    #         decimals = contract.functions.decimals().call()
            
    #         # Get raw balance
    #         raw_balance = contract.functions.balanceOf(wallet_address).call()
            
    #         # Convert to proper decimal places
    #         token_balance = raw_balance / (10 ** decimals)
            
    #         balances[token_symbol] = token_balance
            
    #     except Exception as e:
    #         balances[token_symbol] = f"Error: {str(e)}"
    
    return balances