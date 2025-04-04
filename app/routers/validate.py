from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.validate_service import validate_transaction
from app.dependencies import get_network
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ValidateRequest(BaseModel):
    tx_hex: str
    network: str = None

@router.post("/")
def validate_tx(request: ValidateRequest):
    """
    Valida uma transação Bitcoin.
    
    - **tx_hex**: Transação em formato hexadecimal
    - **network**: Rede Bitcoin (testnet ou mainnet)
    
    Retorna resultado da validação, incluindo se a estrutura é válida 
    e se há saldo suficiente.
    """
    try:
        # Se a rede não for fornecida, usar a configuração global
        network = request.network or get_network()
        
        # Validar a transação
        result = validate_transaction(
            tx_hex=request.tx_hex,
            network=network
        )
        
        return result
    except Exception as e:
        logger.error(f"Erro na rota de validação: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e)) 