from fastapi import APIRouter
from app.models.tx_models import TransactionRequest, TransactionResponse
from app.services.tx_service import build_transaction
from app.dependencies import get_network

router = APIRouter()

@router.post("/")
def create_transaction(request: TransactionRequest) -> TransactionResponse:
    network = get_network()
    return build_transaction(request, network)