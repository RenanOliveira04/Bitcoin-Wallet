import asyncio
import sys
from app.services.tx_status_service import get_transaction_status

def main():
    if len(sys.argv) != 2:
        print("Usage: python check_tx_status.py <transaction_id>")
        sys.exit(1)
        
    txid = sys.argv[1]
    print(f"Checking status for transaction: {txid}")
    
    try:
        # Check testnet first (since that's where the transaction was sent)
        print("\nChecking testnet...")
        status = get_transaction_status(txid, network="testnet", force_refresh=True)
        print(f"Status: {status.status}")
        print(f"Confirmations: {status.confirmations}")
        print(f"Block Height: {status.block_height}")
        print(f"Explorer URL: {status.explorer_url}")
        
    except Exception as e:
        print(f"\nError checking testnet: {str(e)}")
        print("\nChecking mainnet...")
        try:
            status = get_transaction_status(txid, network="mainnet", force_refresh=True)
            print(f"Status: {status.status}")
            print(f"Confirmations: {status.confirmations}")
            print(f"Block Height: {status.block_height}")
            print(f"Explorer URL: {status.explorer_url}")
        except Exception as e2:
            print(f"Error checking mainnet: {str(e2)}")

if __name__ == "__main__":
    main()
