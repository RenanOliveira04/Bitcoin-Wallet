from abc import ABC, abstractmethod
from bitcoinlib.transactions import Transaction
from app.models.utxo_models import TransactionRequest, TransactionResponse
import logging

logger = logging.getLogger(__name__)

class TransactionBuilder(ABC):
    @abstractmethod
    def build(self, request: TransactionRequest, network: str) -> TransactionResponse:
        pass

class BitcoinLibBuilder(TransactionBuilder):
    def build(self, request: TransactionRequest, network: str) -> TransactionResponse:
        logger.info(f"Iniciando construção de transação para rede {network}")
        try:
            formatted_inputs = []
            for input_tx in request.inputs:
                formatted_input = {
                    "txid": input_tx.txid,
                    "output_n": input_tx.vout,
                }
                if input_tx.script:
                    formatted_input["script"] = input_tx.script
                if input_tx.value:
                    formatted_input["value"] = input_tx.value
                if input_tx.sequence:
                    formatted_input["sequence"] = input_tx.sequence
                formatted_inputs.append(formatted_input)
            
            formatted_outputs = []
            for output in request.outputs:
                formatted_outputs.append({
                    "address": output.address,
                    "value": output.value
                })
            
            tx = Transaction(
                inputs=formatted_inputs,
                outputs=formatted_outputs,
                network=network,
                fee=request.fee_rate
            )
            response = TransactionResponse(
                raw_transaction=tx.raw_hex(),
                txid=tx.txid
            )
            logger.debug("Transação construída com sucesso", extra={
                "txid": tx.txid,
                "network": network
            })
            return response
        except Exception as e:
            logger.error("Erro ao construir transação", exc_info=True)
            raise 