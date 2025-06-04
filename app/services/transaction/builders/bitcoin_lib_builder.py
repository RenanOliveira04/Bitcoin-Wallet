from abc import ABC, abstractmethod
from bitcoinlib.transactions import Transaction, Input, Output
from app.models.utxo_models import TransactionRequest, TransactionResponse
from app.services.sign_service import sign_transaction
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
            if not request.inputs or len(request.inputs) == 0:
                raise ValueError("Nenhum input fornecido para a transação")
                
            logger.info(f"Construindo transação com {len(request.inputs)} inputs e {len(request.outputs)} outputs")
            
            tx_inputs = []
            for i, input_tx in enumerate(request.inputs):
                try:
                    if not input_tx.txid or input_tx.vout is None:
                        raise ValueError(f"Input {i} está faltando txid ou vout")
                        
                    logger.debug(f"Processando input {i}: txid={input_tx.txid}, vout={input_tx.vout}, value={input_tx.value}")
                    
                    tx_input = Input(
                        prev_txid=input_tx.txid,
                        output_n=input_tx.vout,
                        unlocking_script=input_tx.script if hasattr(input_tx, 'script') and input_tx.script else b'',
                        witness_type='segwit',
                        network=network
                    )
                    
                    if hasattr(input_tx, 'value') and input_tx.value:
                        tx_input.value = input_tx.value
                        
                    if hasattr(input_tx, 'sequence') and input_tx.sequence:
                        tx_input.sequence = input_tx.sequence
                        
                    tx_inputs.append(tx_input)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar input {i}: {str(e)}", exc_info=True)
                    raise ValueError(f"Erro no input {i}: {str(e)}")
            
            tx_outputs = []
            for i, output in enumerate(request.outputs):
                try:
                    if not output.address or output.value is None:
                        raise ValueError(f"Output {i} está faltando endereço ou valor")
                        
                    logger.debug(f"Processando output {i}: address={output.address}, value={output.value}")
                    
                    tx_output = Output(
                        value=output.value,
                        address=output.address,
                        network=network
                    )
                    tx_outputs.append(tx_output)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar output {i}: {str(e)}", exc_info=True)
                    raise ValueError(f"Erro no output {i}: {str(e)}")
            
            fee = max(1.0, float(request.fee_rate or 1.0))
            logger.info(f"Configurando taxa para {fee} sat/byte")
            
            logger.info(f"Creating transaction with {len(tx_inputs)} inputs and {len(tx_outputs)} outputs")
            for i, inp in enumerate(tx_inputs):
                logger.info(f"Input {i}: txid={inp.prev_txid}, "
                           f"output_n={inp.output_n}, "
                           f"value={getattr(inp, 'value', 'N/A')}, "
                           f"unlocking_script={inp.unlocking_script.hex() if inp.unlocking_script else 'None'}, "
                           f"witness_type={getattr(inp, 'witness_type', 'N/A')}, "
                           f"sequence={getattr(inp, 'sequence', 'N/A')}")
            logger.info(f"Creating transaction with parameters: version=2, locktime=0, network={network}, "
                       f"fee={fee}, fee_per_kb={int(fee * 1000)}, witness_type=segwit")
            try:
                tx = Transaction(
                    version=2,
                    locktime=0,
                    network=network,
                    fee=fee,
                    fee_per_kb=int(fee * 1000),
                    witness_type='segwit'
                )
                
                # Add all inputs first
                for tx_input in tx_inputs:
                    output_n = tx_input.output_n
                    if isinstance(output_n, bytes):
                        output_n = int.from_bytes(output_n, byteorder='little')
                    
                    # Create input with minimal required fields
                    tx.add_input(
                        prev_txid=tx_input.prev_txid,
                        output_n=output_n,
                        witness_type='segwit'
                    )
                    
                    # Set additional input properties after adding
                    input_index = len(tx.inputs) - 1
                    if hasattr(tx_input, 'value') and tx_input.value is not None:
                        tx.inputs[input_index].value = tx_input.value
                    
                    if hasattr(tx_input, 'script') and tx_input.script:
                        tx.inputs[input_index].script = tx_input.script
                        
                    # Log the added input for debugging
                    logger.debug(f"Added input: txid={tx_input.prev_txid}, output_n={output_n}, "
                               f"value={getattr(tx_input, 'value', 'N/A')}")
                
                for output in tx_outputs:
                    tx.add_output(value=output.value, address=output.address)
                
                tx.fee = fee
                tx.fee_per_kb = int(fee * 1000)
                
                logger.info("Transaction object created successfully")
                
                if not tx.inputs or len(tx.inputs) == 0:
                    raise ValueError("Transaction has no inputs after creation")
                
                for i, tx_input in enumerate(tx_inputs):
                    if hasattr(tx_input, 'private_key') and tx_input.private_key:
                        tx.sign(keys=tx_input.private_key, index=i)
                        logger.info(f"Signed input {i} with provided private key")
                    else:
                        logger.warning(f"No private key provided for input {i}, transaction will need to be signed separately")
                    
                if not tx.outputs or len(tx.outputs) == 0:
                    raise ValueError("Transaction has no outputs after creation")
                    
            except Exception as e:
                logger.error(f"Error creating transaction: {str(e)}", exc_info=True)
                raise
                
            tx.update_totals()
            
            logger.info(f"Transaction created with {len(tx.inputs)} inputs and {len(tx.outputs)} outputs")
            
            for i, inp in enumerate(tx.inputs):
                logger.debug(f"Input {i}: txid={inp.prev_txid.hex() if hasattr(inp.prev_txid, 'hex') else inp.prev_txid}, "
                           f"output_n={inp.output_n}, value={getattr(inp, 'value', 'N/A')}")
            
            raw_tx = None
            if hasattr(request, 'private_key') and request.private_key:
                logger.info("Signing transaction with provided private key")
                try:
                    if not tx.inputs:
                        raise ValueError("No inputs to sign in transaction")
                    
                    for i in range(len(tx.inputs)):
                        logger.debug(f"Signing input {i}")
                        try:
                            tx.sign(keys=request.private_key, index=i)
                            logger.debug(f"Successfully signed input {i}")
                        except Exception as e:
                            logger.warning(f"Failed to sign input {i}: {str(e)}")
                            raise
                    
                    raw_tx = tx.raw_hex()
                    logger.info(f"Transaction signed successfully, raw size: {len(raw_tx)//2} bytes")
                    
                    try:
                        parsed_tx = Transaction.parse_hex(raw_tx, strict=False)
                        if not parsed_tx.inputs:
                            raise ValueError("Transaction has no inputs after signing")
                        logger.debug(f"Verified signed transaction has {len(parsed_tx.inputs)} inputs")
                    except Exception as e:
                        logger.error(f"Failed to verify signed transaction: {str(e)}")
                        raise
                    
                except Exception as e:
                    logger.error(f"Error signing transaction: {str(e)}", exc_info=True)
                    try:
                        raw_tx = tx.raw_hex()
                        logger.warning(f"Generated raw transaction (may be unsigned): {raw_tx[:100]}...")
                    except Exception as e2:
                        logger.error(f"Failed to generate raw transaction: {str(e2)}")
                        raise ValueError(f"Failed to generate transaction: {str(e2)}")
                    
                    if "--debug" in sys.argv:
                        raise ValueError(f"Failed to sign transaction: {str(e)}")
            else:
                logger.warning("No private key provided, generating unsigned transaction")
                try:
                    raw_tx = tx.raw_hex()
                    logger.info(f"Generated unsigned transaction: {raw_tx[:100]}...")
                except Exception as e:
                    logger.error(f"Failed to generate raw transaction: {str(e)}")
                    raise ValueError(f"Failed to generate transaction: {str(e)}")
                
            if not raw_tx:
                raise ValueError("Failed to generate raw transaction")
            
            try:
                from bitcoinlib.transactions import Transaction as BCLTransaction
                parsed_tx = BCLTransaction.parse_hex(raw_tx, strict=False)
                
                if len(parsed_tx.inputs) != len(tx.inputs):
                    error_msg = f"Input count mismatch after serialization: {len(parsed_tx.inputs)} != {len(tx.inputs)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                    
                logger.info("Transaction serialization verified successfully")
                
                if not tx.outputs or len(tx.outputs) == 0:
                    raise ValueError("Transaction has no outputs after creation")
                    
            except Exception as e:
                logger.error(f"Error verifying transaction serialization: {str(e)}", exc_info=True)
                raise ValueError(f"Failed to verify transaction serialization: {str(e)}")
                
            logger.info(f"Transaction created with {len(tx.inputs)} inputs and {len(tx.outputs)} outputs")
            for i, inp in enumerate(tx.inputs):
                logger.debug(f"Input {i}: txid={inp.prev_txid.hex() if hasattr(inp.prev_txid, 'hex') else inp.prev_txid}, "
                           f"output_n={inp.output_n}, value={inp.value}")
                
            for i, out in enumerate(tx.outputs):
                logger.debug(f"Output {i}: address={out.address}, value={out.value}")
            
            raw_tx = tx.raw_hex()
            logger.info(f"Raw transaction generated, length: {len(raw_tx)} bytes")
            
            if not tx.txid:
                raise ValueError("Falha ao gerar TXID para a transação")
            
            if not raw_tx or len(raw_tx) < 64:
                raise ValueError(f"Transação raw inválida gerada: {raw_tx}")
            
            try:
                from bitcoinlib.transactions import Transaction as BCLTransaction
                
                parsed_tx = BCLTransaction.parse_hex(raw_tx)
                
                if len(parsed_tx.inputs) != len(tx_inputs):
                    error_msg = (
                        f"Número incorreto de inputs na transação serializada: "
                        f"{len(parsed_tx.inputs)} != {len(tx_inputs)}"
                    )
                    logger.error(f"[VALIDATION] {error_msg}")
                    logger.error(f"[VALIDATION] Raw tx: {raw_tx}")
                    
                    for i, inp in enumerate(tx_inputs):
                        logger.error(f"[VALIDATION] Expected input {i}: txid={inp.prev_txid} vout={inp.output_n}")
                    
                    raise ValueError(error_msg)
                    
                if len(parsed_tx.outputs) != len(tx_outputs):
                    error_msg = (
                        f"Número incorreto de outputs na transação serializada: "
                        f"{len(parsed_tx.outputs)} != {len(tx_outputs)}"
                    )
                    logger.error(f"[VALIDATION] {error_msg}")
                    raise ValueError(error_msg)
                
                logger.info(f"[VALIDATION] Transaction validation successful: {len(parsed_tx.inputs)} inputs, {len(parsed_tx.outputs)} outputs")
                
            except Exception as e:
                logger.error(f"[VALIDATION] Erro ao verificar transação serializada: {str(e)}", exc_info=True)
                logger.error(f"[VALIDATION] Raw transaction hex: {raw_tx}")
                raise ValueError(f"Falha na validação da transação serializada: {str(e)}")
            
            calculated_fee = 0
            if tx.input_total and tx.output_total:
                calculated_fee = tx.input_total - tx.output_total
                if calculated_fee <= 0:
                    logger.warning(f"Taxa calculada inválida: {calculated_fee}")
                    calculated_fee = 1  
            
            response = TransactionResponse(
                raw_transaction=raw_tx,
                txid=str(tx.txid),
                fee=calculated_fee
            )
            
            logger.info(f"Transação construída com sucesso: {tx.txid}", extra={
                "txid": str(tx.txid),
                "network": network,
                "fee": calculated_fee,
                "size_bytes": len(raw_tx) // 2  
            })
            
            return response
            
        except ValueError as ve:
            logger.error(f"Erro de validação: {str(ve)}", exc_info=True)
            raise
        except Exception as e:
            logger.error("Erro inesperado ao construir transação", exc_info=True)
            raise Exception(f"Falha ao construir transação: {str(e)}")