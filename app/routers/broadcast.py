from fastapi import APIRouter
import requests
from app.dependencies import get_blockchain_api_url

router = APIRouter()

@router.post("/")
def broadcast_transaction(raw_tx: str):
    url = f"{get_blockchain_api_url()}/tx"
    response = requests.post(url, json={"tx": raw_tx})
    return {
        "status": response.status_code,
        "explorer_url": f"https://blockchair.com/tx/{response.json()['txid']}"
    }