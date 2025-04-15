import logging
from typing import Dict, Any

from app.models.utxo_models import TransactionRequest, TransactionResponse, Input, Output
from app.services.transaction import BitcoinLibBuilder
from app.services.transaction.validators.transaction_validator import TransactionValidator

logger = logging.getLogger(__name__)

def build_transaction(tx_request: TransactionRequest, network: str) -> TransactionResponse:
    """
    Constrói uma transação Bitcoin não assinada.
    
    Esta função valida os inputs e outputs da transação e utiliza o BitcoinLibBuilder
    para construir uma transação Bitcoin não assinada que pode ser posteriormente assinada
    e transmitida para a rede.
    
    Args:
        tx_request (TransactionRequest): Dados da requisição contendo inputs e outputs
        network (str): Rede Bitcoin (mainnet ou testnet)
        
    Returns:
        TransactionResponse: Resposta contendo a transação raw em formato hexadecimal e o txid
        
    Raises:
        Exception: Se ocorrer algum erro durante a construção da transação
    """
    try:
        logger.info(f"[TX_BUILD] Iniciando construção de transação para rede {network}")
        
        # Validar inputs e outputs
        TransactionValidator.validate_inputs(tx_request.inputs)
        TransactionValidator.validate_outputs(tx_request.outputs)
        
        # Verificar e garantir que objetos Input e Output estão corretos
        # Isso é necessário porque o FastAPI pode deserializar para dicionários
        # em vez de objetos Input/Output em alguns casos
        if not all(isinstance(i, Input) for i in tx_request.inputs):
            logger.warning("[TX_BUILD] Convertendo dicionários de inputs para objetos Input")
            inputs = []
            for i in tx_request.inputs:
                if isinstance(i, dict):
                    inputs.append(Input(**i))
                else:
                    inputs.append(i)
            tx_request.inputs = inputs
            
        if not all(isinstance(o, Output) for o in tx_request.outputs):
            logger.warning("[TX_BUILD] Convertendo dicionários de outputs para objetos Output")
            outputs = []
            for o in tx_request.outputs:
                if isinstance(o, dict):
                    outputs.append(Output(**o))
                else:
                    outputs.append(o)
            tx_request.outputs = outputs
        
        tx_builder = BitcoinLibBuilder()
        response = tx_builder.build(tx_request, network)
        
        logger.info(f"[TX_BUILD] Transação construída com sucesso: {response.txid}")
        return response
        
    except Exception as e:
        logger.error(f"[TX_BUILD] Erro ao construir transação: {str(e)}", exc_info=True)
        raise Exception(f"Erro ao construir transação: {str(e)}") 