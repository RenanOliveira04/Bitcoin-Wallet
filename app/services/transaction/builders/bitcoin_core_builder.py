from bitcoin.core import CMutableTxIn, CMutableTxOut, CMutableTransaction, b2x
from bitcoin.core.script import CScript
import logging
from typing import Optional, Any

from app.models.utxo_models import TransactionRequest, TransactionResponse
from app.services.transaction.builders.bitcoin_lib_builder import TransactionBuilder

logger = logging.getLogger(__name__)

class BitcoinCoreBuilder(TransactionBuilder):
    """
    Implementação do TransactionBuilder usando a biblioteca python-bitcoinlib.
    Esta classe cria transações Bitcoin utilizando a biblioteca python-bitcoinlib que
    implementa protocolos do Bitcoin Core.
    """
    
    def __init__(self, rpc_connection: Optional[Any] = None):
        """
        Inicializa o construtor com uma conexão RPC opcional.
        
        Args:
            rpc_connection: Conexão RPC com um nó Bitcoin (opcional)
        """
        self.rpc = rpc_connection
    
    def build(self, request: TransactionRequest, network: str) -> TransactionResponse:
        """
        Constrói uma transação Bitcoin usando a biblioteca python-bitcoinlib.
        
        Args:
            request: Dados da requisição contendo inputs e outputs
            network: Rede Bitcoin (mainnet ou testnet)
            
        Returns:
            TransactionResponse: Resposta contendo a transação raw em formato hexadecimal e o txid
            
        Raises:
            Exception: Se ocorrer algum erro durante a construção da transação
        """
        logger.info(f"Iniciando construção de transação Bitcoin Core para rede {network}")
        try:
            import bitcoin
            
            # Use a helper method for selecting chain parameters
            # This makes it easier to mock in tests
            self.select_chain_params(network)
            
            tx_inputs = []
            input_total = 0
            for input_tx in request.inputs:
                txid_bytes = bytes.fromhex(input_tx.txid)[::-1]  
                
                tx_in = CMutableTxIn(prevout=(txid_bytes, input_tx.vout))
                
                if input_tx.script:
                    tx_in.scriptSig = CScript(bytes.fromhex(input_tx.script))
                
                if input_tx.sequence is not None:
                    tx_in.nSequence = input_tx.sequence
                
                tx_inputs.append(tx_in)
                
                if input_tx.value:
                    input_total += input_tx.value
            
            tx_outputs = []
            output_total = 0
            for output in request.outputs:
                amount = output.value
                output_total += amount
                
                tx_out = CMutableTxOut(amount)
                
                if self.rpc:
                    tx_out.scriptPubKey = self.rpc.validateaddress(output.address)["scriptPubKey"]
                else:
                    from bitcoin.wallet import CBitcoinAddress
                    addr = CBitcoinAddress(output.address)
                    tx_out.scriptPubKey = addr.to_scriptPubKey()
                
                tx_outputs.append(tx_out)
            
            tx = CMutableTransaction(tx_inputs, tx_outputs)
            
            # Use a helper method for calculating fee
            # This makes it easier to mock in tests
            calculated_fee = self.calculate_tx_fee(input_total, output_total)
            
            raw_tx_hex = b2x(tx.serialize())
            
            txid = b2x(tx.GetTxid()[::-1])  # Reverte bytes devido ao endianness
            
            response = TransactionResponse(
                raw_transaction=raw_tx_hex,
                txid=txid,
                fee=calculated_fee
            )
            
            logger.debug("Transação Bitcoin Core construída com sucesso", extra={
                "txid": txid,
                "network": network,
                "fee": calculated_fee
            })
            
            return response
        except Exception as e:
            logger.error("Erro ao construir transação com Bitcoin Core", exc_info=True)
            raise Exception(f"Erro ao construir transação com Bitcoin Core: {str(e)}")
    
    def select_chain_params(self, network: str) -> None:
        """
        Selects the appropriate Bitcoin chain parameters based on the network.
        This method is exposed separately to make it easier to mock in tests.
        
        Args:
            network: The Bitcoin network ("mainnet" or "testnet")
        """
        import bitcoin
        if network == "testnet":
            bitcoin.SelectParams("testnet")
        else:
            bitcoin.SelectParams("mainnet")
    
    def calculate_tx_fee(self, input_total: int, output_total: int) -> int:
        """
        Calculates the transaction fee as the difference between inputs and outputs.
        This method is exposed separately to make it easier to mock in tests.
        
        Args:
            input_total: The total input amount in satoshis
            output_total: The total output amount in satoshis
            
        Returns:
            int: The calculated fee in satoshis
        """
        return input_total - output_total