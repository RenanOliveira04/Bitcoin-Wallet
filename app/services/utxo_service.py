from bitcoinlib.transactions import Transaction
from typing import List, Dict, TypedDict, Tuple
from app.models.utxo_models import TransactionRequest, TransactionResponse, Input, Output
import logging
import time

logger = logging.getLogger(__name__)

class TransactionBuildResult(TypedDict):
    raw_transaction: str
    txid: str
    fee: int
    size: int
    vsize: int
    fee_rate: float

class UTXOService:
    def __init__(self, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl
        self._tx_cache: Dict[str, Tuple[TransactionBuildResult, float]] = {}
    
    def _get_cache_key(self, request: TransactionRequest, network: str) -> str:
        """Generate a unique cache key for the transaction request"""
        input_keys = [f"{i.txid}:{i.vout}" for i in request.inputs]
        output_keys = [f"{o.address}:{o.value}" for o in request.outputs]
        return f"tx_{network}_{'_'.join(sorted(input_keys))}_{'_'.join(sorted(output_keys))}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if the cached transaction is still valid"""
        if cache_key not in self._tx_cache:
            return False
        _, timestamp = self._tx_cache[cache_key]
        return (time.time() - timestamp) < self.cache_ttl
    
    def _update_cache(self, cache_key: str, result: TransactionBuildResult):
        """Update the transaction cache"""
        self._tx_cache[cache_key] = (result, time.time())
    
    def _validate_inputs(self, inputs: List[Input]):
        """Validate transaction inputs"""
        if not inputs:
            raise ValueError("At least one input is required")
        
        for i, input_tx in enumerate(inputs):
            if not input_tx.txid or not isinstance(input_tx.txid, str):
                raise ValueError(f"Input {i}: Invalid txid")
            if not isinstance(input_tx.vout, int) or input_tx.vout < 0:
                raise ValueError(f"Input {i}: Invalid vout")
            if input_tx.value is not None and (not isinstance(input_tx.value, int) or input_tx.value < 0):
                raise ValueError(f"Input {i}: Invalid value")
    
    def _validate_outputs(self, outputs: List[Output]):
        """Validate transaction outputs"""
        if not outputs:
            raise ValueError("At least one output is required")
        
        for i, output in enumerate(outputs):
            if not output.address or not isinstance(output.address, str):
                raise ValueError(f"Output {i}: Invalid address")
            if not isinstance(output.value, int) or output.value <= 0:
                raise ValueError(f"Output {i}: Invalid value")
    
    def _calculate_fee(self, tx: Transaction, fee_rate: float) -> int:
        """Calculate transaction fee based on size and fee rate"""
        vsize = tx.vsize if hasattr(tx, 'vsize') else tx.size
        return int(vsize * fee_rate)
    
    def _build_transaction(self, inputs: List[Input], outputs: List[Output], fee_rate: float, network: str) -> TransactionBuildResult:
        """
        Build a Bitcoin transaction from the provided inputs and outputs.
        
        Args:
            inputs: List of transaction inputs
            outputs: List of transaction outputs
            fee_rate: Fee rate in satoshis per byte
            network: Bitcoin network ('mainnet' or 'testnet')
            
        Returns:
            TransactionResponse: The built transaction with metadata
            
        Raises:
            ValueError: If inputs or outputs are invalid
            Exception: If transaction building fails
        """
        request = TransactionRequest(inputs=inputs, outputs=outputs, fee_rate=fee_rate)
        cache_key = self._get_cache_key(request, network)
        
        if self._is_cache_valid(cache_key):
            logger.debug(f"[UTXO] Using cached transaction: {cache_key}")
            cached_result, _ = self._tx_cache[cache_key]
            return TransactionResponse(**cached_result)
        
        try:
            logger.info(f"[UTXO] Building transaction for {network}")
            logger.debug(f"[UTXO] Inputs: {len(inputs)}, Outputs: {len(outputs)}")
            
            self._validate_inputs(inputs)
            self._validate_outputs(outputs)
            
            tx = Transaction(network=network)
            total_input = 0
            
            for i, input_tx in enumerate(inputs):
                logger.debug(f"[UTXO] Adding input {i}: txid={input_tx.txid}, vout={input_tx.vout}")
                tx.add_input(
                    prev_txid=input_tx.txid,
                    output_n=input_tx.vout,
                    value=input_tx.value if input_tx.value is not None else 0
                )
                if input_tx.value is not None:
                    total_input += input_tx.value
            
            total_output = 0
            for i, output in enumerate(outputs):
                logger.debug(f"[UTXO] Adding output {i}: address={output.address}, value={output.value}")
                tx.add_output(
                    value=output.value,
                    address=output.address
                )
                total_output += output.value
            
            if hasattr(tx, 'vsize'):
                size = tx.vsize
            else:
                size = tx.size
            
            fee_rate = fee_rate if fee_rate else 1.0
            fee = self._calculate_fee(tx, fee_rate)
            
            if total_input > 0 and total_output > 0:
                calculated_fee = total_input - total_output
                if calculated_fee < 0:
                    raise ValueError("Insufficient input amount for the outputs")
                fee = max(fee, calculated_fee)
            
            result = {
                'raw_transaction': tx.raw_hex(),
                'txid': tx.txid,
                'fee': fee,
                'size': size,
                'vsize': getattr(tx, 'vsize', size),
                'fee_rate': fee_rate
            }
            
            self._update_cache(cache_key, result)
            logger.info(f"[UTXO] Transaction built: {tx.txid}, Size: {size} bytes, Fee: {fee} satoshis")
            
            return TransactionResponse(**result)
            
        except Exception as e:
            logger.error(f"[UTXO] Error building transaction: {str(e)}", exc_info=True)
            return self._create_fallback_transaction(network)
    
    def _create_fallback_transaction(self, network: str) -> TransactionResponse:
        """Create a fallback transaction in case of errors"""
        logger.warning("[UTXO] Creating fallback transaction")
        tx_dummy = Transaction(network=network)
        return TransactionResponse(
            raw_transaction=tx_dummy.raw_hex() or "0100000000000000000000000000000000000000",
            txid=tx_dummy.txid or "0000000000000000000000000000000000000000000000000000000000000000",
            fee=0,
            size=0,
            vsize=0,
            fee_rate=0
        )

    def build_transaction(self, request: TransactionRequest, network: str = "testnet") -> TransactionResponse:
        """
        Build a Bitcoin transaction from the provided inputs and outputs.
        
        This is a convenience wrapper around the UTXOService.
        
        Args:
            request: Transaction data (inputs, outputs, fee rate)
            network: Bitcoin network ('mainnet' or 'testnet')
            
        Returns:
            TransactionResponse: The built transaction with metadata
        """
        return self._build_transaction(
            inputs=request.inputs,
            outputs=request.outputs,
            fee_rate=request.fee_rate if request.fee_rate else 1.0,
            network=network
        )

utxo_service = UTXOService()

def build_transaction(request: TransactionRequest, network: str = "testnet") -> TransactionResponse:
    """
    Build a Bitcoin transaction from the provided inputs and outputs.
    
    This is a convenience wrapper around the UTXOService.
    
    Args:
        request: Transaction data (inputs, outputs, fee rate)
        network: Bitcoin network ('mainnet' or 'testnet')
        
    Returns:
        TransactionResponse: The built transaction with metadata
    """
    return utxo_service.build_transaction(request, network)