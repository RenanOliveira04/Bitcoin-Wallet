from app.services.transaction import BitcoinLibBuilder, TransactionValidator
from app.models.utxo_models import TransactionRequest, TransactionResponse
import logging

logger = logging.getLogger(__name__)

def build_transaction(request: TransactionRequest, network: str) -> TransactionResponse:
    logger.info("Iniciando processo de construção de transação")
    
    # Validação
    validator = TransactionValidator()
    validator.validate_inputs(request.inputs)
    validator.validate_outputs(request.outputs)
    
    # Construção
    builder = BitcoinLibBuilder()
    return builder.build(request, network)