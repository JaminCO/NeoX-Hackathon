import requests

# NEO X RPC endpoint for querying blocks/transactions
rpc_url = "https://neoxt4seed1.ngd.network"  # Replace with your RPC endpoint

# Wallet to monitor
wallet_address = "0xa80CDa9D4898E2Cb232453ded54Fcb56b03e01Ae"


# Example function to fetch transactions involving the address
def get_transactions(address):
    params = {
        "jsonrpc": "2.0",
        "method": "eth_getLogs",  # Assuming you can use a similar method for NEO X
        "params": [{
            "address": address,
            "fromBlock": "latest",
            "toBlock": "latest",
        }],
        "id": 1
    }

    while True:
        response = requests.post(rpc_url, json=params)
        if response.status_code == 200:
            result = response.json()
            print(result)
        else:
            print("Error fetching transactions:", response.status_code)

# Example usage
get_transactions(wallet_address)
