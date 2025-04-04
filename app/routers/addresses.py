from fastapi import APIRouter, HTTPException, Query
from app.models.address_models import AddressFormat
from app.services.address_service import generate_address
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{address_format}")
def get_address(
    private_key: str,
    address_format: AddressFormat,
    network: str = Query("testnet", description="mainnet ou testnet")
):
    """
    Gera um endereço Bitcoin no formato especificado
    
    Args:
        private_key: Chave privada em formato hexadecimal
        address_format: Formato do endereço (p2pkh, p2sh, p2wpkh, p2tr)
        network: Rede Bitcoin (mainnet ou testnet)
        
    Returns:
        Dicionário com endereço, formato e rede
    """
    try:
        logger.info(f"Gerando endereço {address_format} para rede {network}")
        result = generate_address(private_key, address_format, network)
        return result
    except Exception as e:
        logger.error(f"Erro ao gerar endereço: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))