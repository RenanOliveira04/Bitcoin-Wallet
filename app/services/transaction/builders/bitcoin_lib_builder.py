from abc import ABC, abstractmethod
from bitcoinlib.transactions import Transaction
from app.models.tx_models import TransactionRequest, TransactionResponse
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
            tx = Transaction(
                inputs=request.inputs,
                outputs=request.outputs,
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