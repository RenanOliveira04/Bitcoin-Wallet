from fastapi import APIRouter, HTTPException, Query
from app.services.tx_status_service import get_transaction_status
from app.dependencies import get_network
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{txid}")
def get_tx_status(
    txid: str,
    network: str = Query(None, description="Rede Bitcoin: mainnet ou testnet")
):
    """
    Consulta o status de uma transação Bitcoin.
    
    - **txid**: ID da transação a ser consultada
    - **network**: Rede Bitcoin (testnet ou mainnet)
    
    Retorna o status atual da transação, confirmações e link para explorador.
    """
    try:
        # Se a rede não for fornecida, usar a configuração global
        if not network:
            network = get_network()
        
        # Consultar o status
        result = get_transaction_status(txid, network)
        
        return result
    except Exception as e:
        logger.error(f"Erro na rota de status de transação: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e)) 