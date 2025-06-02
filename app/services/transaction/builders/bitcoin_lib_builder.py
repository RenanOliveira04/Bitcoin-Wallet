from abc import ABC, abstractmethod
from bitcoinlib.transactions import Transaction, Input, Output
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
            tx_inputs = []
            for input_tx in request.inputs:
                tx_input = Input(
                    prev_txid=input_tx.txid,
                    output_n=input_tx.vout,
                    value=input_tx.value or 0,  
                    address=input_tx.address,
                    network=network
                )
                if input_tx.script:
                    tx_input.script = input_tx.script
                if input_tx.sequence:
                    tx_input.sequence = input_tx.sequence
                tx_inputs.append(tx_input)
            
            tx_outputs = []
            for output in request.outputs:
                tx_output = Output(
                    value=output.value,
                    address=output.address,
                    network=network
                )
                tx_outputs.append(tx_output)
            
            fee = request.fee_rate or 1.0
            tx = Transaction(
                inputs=tx_inputs,
                outputs=tx_outputs,
                network=network,
                fee=fee,
                fee_per_kb=int(fee * 1000)  
            )
            
            calculated_fee = 0
            if tx.input_total and tx.output_total:
                calculated_fee = tx.input_total - tx.output_total
            
            # Ensure txid is a string (handles mock objects in tests)
            txid = str(tx.txid) if tx.txid else ""

            # Create the response object
            response = TransactionResponse(
                raw_transaction=tx.raw_hex(),
                txid=txid,
                fee=calculated_fee
            )
            
            logger.debug("Transação construída com sucesso", extra={
                "txid": txid,
                "network": network,
                "fee": calculated_fee
            })
            
            return response
        except Exception as e:
            logger.error("Erro ao construir transação", exc_info=True)
            raise 