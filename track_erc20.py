from web3 import Web3

# Connect to Neo X node
w3 = Web3(Web3.HTTPProvider("https://neoxt4seed1.ngd.network"))

# ERC-20 Token contract address and Transfer event signature
token_contract_address = '0xYourTokenContractAddress'  # Replace with the actual token contract address
transfer_event_signature = w3.keccak(text='Transfer(address,address,uint256)').hex()

# Create a filter for the Transfer event
filter = w3.eth.filter({
    'address': token_contract_address,  # Token contract address
    'topics': [transfer_event_signature]  # Filter by Transfer event
})

# Monitor for new token transfers
def monitor_token_transfers():
    while True:
        logs = w3.eth.get_filter_changes(filter.filter_id)
        for log in logs:
            # Decode the log data
            decoded_log = w3.eth.abi.decode_log([{
                'type': 'address',
                'name': 'from'
            }, {
                'type': 'address',
                'name': 'to'
            }, {
                'type': 'uint256',
                'name': 'value'
            }], log['data'], log['topics'][1:])
            
            # Check the token transfer details
            from_address = decoded_log['from']
            to_address = decoded_log['to']
            value = decoded_log['value'] / 10**18  # Assuming 18 decimals for the token
            
            print(f"Token transfer detected:")
            print(f"From: {from_address}")
            print(f"To: {to_address}")
            print(f"Amount: {value} Tokens")

# Start monitoring
monitor_token_transfers()
