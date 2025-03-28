from fastapi import APIRouter
from app.services.blockchain_service import get_balance, get_utxos
from app.dependencies import get_network

router = APIRouter()

@router.get("/{address}")
def get_balance_utxos(address: str):
    network = get_network()
    return {
        "balance": get_balance(address, network),
        "utxos": get_utxos(address, network)
    }