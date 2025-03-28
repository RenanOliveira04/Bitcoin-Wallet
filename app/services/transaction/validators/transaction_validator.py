from typing import List, Dict
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class TransactionValidator:
    @staticmethod
    def validate_inputs(inputs: List[Dict[str, str]]) -> None:
        logger.debug("Validando inputs da transação")
        if not inputs:
            logger.error("Inputs vazios")
            raise HTTPException(status_code=400, detail="Inputs não podem estar vazios")
        
        for input in inputs:
            if "txid" not in input or "vout" not in input:
                logger.error(f"Input inválido: {input}")
                raise HTTPException(status_code=400, detail="Input inválido: necessário txid e vout")

    @staticmethod
    def validate_outputs(outputs: List[Dict[str, str]]) -> None:
        logger.debug("Validando outputs da transação")
        if not outputs:
            logger.error("Outputs vazios")
            raise HTTPException(status_code=400, detail="Outputs não podem estar vazios")
        
        for output in outputs:
            if "address" not in output or "value" not in output:
                logger.error(f"Output inválido: {output}")
                raise HTTPException(status_code=400, detail="Output inválido: necessário address e value") 