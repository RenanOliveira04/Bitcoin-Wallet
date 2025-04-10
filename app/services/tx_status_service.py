import requests
import logging
from typing import Dict, Any, Optional
from app.models.transaction_status_models import TransactionStatusModel
from app.dependencies import get_bitcoinlib_network, get_blockchain_api_url

logger = logging.getLogger(__name__)

def get_transaction_status(txid: str, network: str = "testnet") -> TransactionStatusModel:
    """
    Consulta o status atual de uma transação Bitcoin na blockchain.
    
    Esta função verifica o estado de uma transação, incluindo se ela foi confirmada,
    em qual bloco, quantas confirmações tem, e quando foi processada.
    
    O ciclo de vida de uma transação Bitcoin inclui:
    1. Transmitida (Mempool): A transação foi enviada para a rede, mas ainda não foi incluída em um bloco
    2. Confirmada (1+ confirmações): A transação foi incluída em um bloco
    3. Estabelecida (6+ confirmações): A transação tem confirmações suficientes para ser considerada irreversível
    
    Args:
        txid (str): ID da transação (hash de 64 caracteres hexadecimais)
        network (str, optional): Rede Bitcoin ('mainnet', 'testnet'). Defaults to "testnet".
    
    Returns:
        TransactionStatusModel: Status atual da transação com informações detalhadas
            Inclui 'status', 'confirmations', 'block_height', etc.
        
    Raises:
        Exception: Se a transação não for encontrada ou ocorrer um erro na consulta
    """
    try:
        logger.info(f"[TX_STATUS] Consultando status da transação {txid}")
        
        # Implementação real
        api_url = get_blockchain_api_url(network)
        response = requests.get(f"{api_url}/transaction/{txid}")
        
        if response.status_code != 200:
            logger.error(f"[TX_STATUS] Erro ao consultar transação: {response.text}")
            raise Exception(f"Transação não encontrada: {txid}")
            
        tx_data = response.json()
        
        confirmations = tx_data.get("confirmations", 0)
        
        if confirmations >= 6:
            status = "confirmed"
        elif confirmations > 0:
            status = "confirming"
        else:
            status = "pending"
            
        explorer_base = "https://blockstream.info/"
        if network == "testnet":
            explorer_base += "testnet/"
        
        return TransactionStatusModel(
            txid=txid,
            status=status,
            confirmations=confirmations,
            block_height=tx_data.get("block_height"),
            block_hash=tx_data.get("block_hash"),
            timestamp=tx_data.get("timestamp"),
            explorer_url=f"{explorer_base}tx/{txid}"
        )
        
    except Exception as e:
        logger.error(f"[TX_STATUS] Erro ao consultar status da transação: {str(e)}")
        raise Exception(f"Erro ao consultar status da transação: {str(e)}")

def _fallback_status(txid: str, network: str, error: str) -> Dict[str, Any]:
    """
    Fornece um status de fallback quando a API falha.
    """
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