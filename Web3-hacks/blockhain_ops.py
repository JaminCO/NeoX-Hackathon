from web3 import Web3

# Connect to an Ethereum node (e.g., Infura, Alchemy, or a local node)
w3 = Web3(Web3.HTTPProvider("https://neoxt4seed1.ngd.network"))

# Check if connected
if w3.is_connected():
    print("Connected to Neo X")
else:
    print("Connection failed")

# Sender's details
sender_address = "0xa80CDa9D4898E2Cb232453ded54Fcb56b03e01Ae"  # Replace with sender's address
private_key = "6860f709908250da81ad3af6ea1b10bf7d8265b63b08e5322cf3da7e4c81a18d"        # Replace with sender's private key

# Recipient's address and amount to send
recipient_address = "0x38A8E09dE82A13fd31Fbe5D19E52BfF46A94f1c9"  # Replace with recipient's address
amount_in_ether = 0.10  # Amount in ETH to send
amount_in_wei = w3.to_wei(amount_in_ether, 'ether')

# Get the nonce (number of transactions sent from the sender address)
nonce = w3.eth.get_transaction_count(sender_address)

# Create the transaction
tx = {
    'nonce': nonce,
    'to': recipient_address,
    'value': amount_in_wei,
    'gas': 21000,  # Standard gas limit for ETH transfers
    'gasPrice': w3.to_wei('30', 'gwei'),  # Replace '30' with current gas price in Gwei
    'chainId': 12227332  # Mainnet chain ID. Use 3, 4, or 5 for testnets like Ropsten, Rinkeby, or Goerli
}

gas_price = w3.eth.gas_price
tx['gasPrice'] = gas_price

# Sign the transaction with the sender's private key
signed_tx = w3.eth.account.sign_transaction(tx, private_key)

# Send the transaction
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

# Get the transaction hash
print(f"Transaction hash: {w3.to_hex(tx_hash)}")

# Optional: Wait for the transaction receipt (to confirm it was mined)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Transaction receipt: {receipt}")

print("\nTransaction Complete")