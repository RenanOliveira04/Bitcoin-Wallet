from typing import List
from fastapi import HTTPException
import logging
from app.models.utxo_models import Input, Output

logger = logging.getLogger(__name__)

class TransactionValidator:
    @staticmethod
    def validate_inputs(inputs: List[Input]) -> None:
        logger.debug("Validando inputs da transação")
        if not inputs:
            logger.error("Inputs vazios")
            raise HTTPException(status_code=400, detail="Inputs não podem estar vazios")
        
        for i, input_tx in enumerate(inputs):
            logger.debug(f"Input {i} validado: txid={input_tx.txid}, vout={input_tx.vout}")

    @staticmethod
    def validate_outputs(outputs: List[Output]) -> None:
        logger.debug("Validando outputs da transação")
        if not outputs:
            logger.error("Outputs vazios")
            raise HTTPException(status_code=400, detail="Outputs não podem estar vazios")
        
        for i, output in enumerate(outputs):
            logger.debug(f"Output {i} validado: address={output.address}, value={output.value}")
            
        for output in outputs:
            if output.value <= 0:
                logger.error(f"Valor de output inválido: {output.value}")
                raise HTTPException(status_code=400, detail="Output com valor inválido: deve ser maior que zero") 