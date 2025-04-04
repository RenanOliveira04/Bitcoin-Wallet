from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.sign_service import sign_transaction
from app.dependencies import get_network
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class SignRequest(BaseModel):
    tx_hex: str
    private_key: str
    network: str = None

@router.post("/")
def sign_tx(request: SignRequest):
    """
    Assina uma transação Bitcoin usando a chave privada fornecida.
    
    - **tx_hex**: Transação em formato hexadecimal
    - **private_key**: Chave privada em formato hexadecimal
    - **network**: Rede Bitcoin (testnet ou mainnet)
    
    Retorna a transação assinada e informações sobre ela.
    """
    try:
        # Se a rede não for fornecida, usar a configuração global
        network = request.network or get_network()
        
        # Assinar a transação
        result = sign_transaction(
            tx_hex=request.tx_hex,
            private_key=request.private_key,
            network=network
        )
        
        return result
    except Exception as e:
        logger.error(f"Erro na rota de assinatura: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e)) 