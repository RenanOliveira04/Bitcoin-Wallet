from fastapi import APIRouter, Query
from app.services.fee_service import get_fee_estimate
from app.dependencies import get_network

router = APIRouter()

@router.get("/estimate")
def estimate_fee(network: str = Query(None, description="Rede Bitcoin: mainnet ou testnet")):
    """
    Retorna a estimativa de taxa atual baseada nas condições da mempool.
    
    - **network**: Rede Bitcoin (mainnet ou testnet). 
                  Se não for fornecido, usa a configuração padrão.
    
    Retorna taxa em sat/vB para diferentes prioridades.
    """
    # Se não for fornecido, usa a configuração global
    if not network:
        network = get_network()
        
    return get_fee_estimate(network) 