import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_transaction_status(txid: str, network: str = "testnet") -> Dict[str, Any]:
    """
    Consulta o status de uma transação na blockchain.
    
    Args:
        txid: ID da transação
        network: Rede Bitcoin (testnet ou mainnet)
        
    Returns:
        Dicionário com detalhes do status da transação
    """
    try:
        logger.info(f"Consultando status da transação {txid} na rede {network}")
        
        if network == "mainnet":
            api_url = f"https://blockstream.info/api/tx/{txid}"
            explorer_url = f"https://blockstream.info/tx/{txid}"
        else:
            api_url = f"https://blockstream.info/testnet/api/tx/{txid}"
            explorer_url = f"https://blockstream.info/testnet/tx/{txid}"
        
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 404:
            logger.info(f"Transação {txid} não encontrada na blockchain")
            return {
                "txid": txid,
                "status": "not_found",
                "confirmations": 0,
                "timestamp": None,
                "explorer_url": explorer_url
            }
        
        response.raise_for_status()
        
        tx_data = response.json()
        
        confirmations = tx_data.get("status", {}).get("confirmed", False)
        block_height = tx_data.get("status", {}).get("block_height")
        block_time = tx_data.get("status", {}).get("block_time")
        
        if confirmations:
            status = "confirmed"
        else:
            status = "mempool"
        
        result = {
            "txid": txid,
            "status": status,
            "confirmations": 1 if confirmations else 0,  # Blockstream não retorna número exato de confirmações
            "block_height": block_height,
            "timestamp": block_time,
            "fee": tx_data.get("fee", 0),
            "size": tx_data.get("size", 0),
            "vsize": tx_data.get("weight", 0) // 4,  # weight/4 é aproximadamente vsize
            "explorer_url": explorer_url
        }
        
        return result
    except Exception as e:
        logger.error(f"Erro ao consultar status da transação: {str(e)}", exc_info=True)
        return _fallback_status(txid, network, str(e))

def _fallback_status(txid: str, network: str, error: str) -> Dict[str, Any]:
    """
    Fornece um status de fallback quando a API falha.
    """
    # URL do explorador apropriado
    if network == "mainnet":
        explorer_url = f"https://blockstream.info/tx/{txid}"
    else:
        explorer_url = f"https://blockstream.info/testnet/tx/{txid}"
    
    return {
        "txid": txid,
        "status": "unknown",
        "confirmations": 0,
        "error": error,
        "explorer_url": explorer_url,
        "note": "Status não disponível - verifique manualmente usando o link do explorador"
    } 