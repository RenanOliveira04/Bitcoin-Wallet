from bitcoinlib.transactions import Transaction
from app.services.blockchain_service import get_utxos
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

def validate_transaction(tx_hex: str, network: str = "testnet") -> Dict[str, Any]:
    """
    Valida a estrutura e o saldo de uma transação Bitcoin.
    
    Args:
        tx_hex: Transação em formato hexadecimal
        network: Rede Bitcoin (testnet ou mainnet)
        
    Returns:
        Dicionário com os resultados da validação
    """
    try:
        logger.info(f"Iniciando validação de transação na rede {network}")
        
        is_valid, structure_issues = validate_structure(tx_hex)
        
        if not is_valid:
            logger.warning(f"Transação inválida: {structure_issues}")
            return {
                "is_valid": False,
                "has_sufficient_funds": False,
                "issues": structure_issues,
                "tx_details": None
            }
        
        tx = Transaction.parse_hex(tx_hex)
        
        has_funds, fund_issues, input_sum, output_sum = validate_funds(tx, network)
        
        tx_details = {
            "txid": tx.txid,
            "version": tx.version,
            "size": tx.size,
            "input_count": len(tx.inputs),
            "output_count": len(tx.outputs),
            "input_total": input_sum,
            "output_total": output_sum,
            "fee": input_sum - output_sum if has_funds else None
        }
        
        result = {
            "is_valid": is_valid,
            "has_sufficient_funds": has_funds,
            "tx_details": tx_details
        }
        
        if fund_issues:
            result["fund_issues"] = fund_issues
            
        logger.info(f"Validação concluída: válida={is_valid}, saldo suficiente={has_funds}")
        return result
    
    except Exception as e:
        logger.error(f"Erro ao validar transação: {str(e)}", exc_info=True)
        return {
            "is_valid": False,
            "has_sufficient_funds": False,
            "error": str(e)
        }

def validate_structure(tx_hex: str) -> Tuple[bool, List[str]]:
    """
    Valida a estrutura básica de uma transação Bitcoin.
    
    Args:
        tx_hex: Transação em formato hexadecimal
        
    Returns:
        Tupla (é_válida, lista_de_problemas)
    """
    issues = []
    
    try:
        if not all(c in '0123456789abcdefABCDEF' for c in tx_hex):
            issues.append("Formato hexadecimal inválido")
            return False, issues
        
        if len(tx_hex) < 20:
            issues.append("Transação muito curta")
            return False, issues
        
        tx = Transaction.parse_hex(tx_hex)
        
        if not tx.inputs or len(tx.inputs) == 0:
            issues.append("Transação não tem inputs")
            return False, issues
        
        if not tx.outputs or len(tx.outputs) == 0:
            issues.append("Transação não tem outputs")
            return False, issues
        
        
        return True, []
    
    except Exception as e:
        issues.append(f"Erro ao analisar transação: {str(e)}")
        return False, issues

def validate_funds(tx: Transaction, network: str) -> Tuple[bool, List[str], int, int]:
    """
    Verifica se os inputs têm fundos suficientes para cobrir os outputs.
    
    Args:
        tx: Objeto de transação
        network: Rede Bitcoin
        
    Returns:
        Tupla (tem_fundos_suficientes, problemas, soma_inputs, soma_outputs)
    """
    issues = []
    input_sum = 0
    output_sum = 0
    
    try:
        for output in tx.outputs:
            output_sum += output.value
        
        for i, tx_input in enumerate(tx.inputs):
            if not hasattr(tx_input, 'prev_txid') or not tx_input.prev_txid:
                issues.append(f"Input {i} não tem TXID anterior")
                continue
                
            address = tx_input.address if hasattr(tx_input, 'address') and tx_input.address else None
            
            if address:
                utxos = get_utxos(address, network)
                
                utxo_found = False
                for utxo in utxos:
                    if utxo.get('txid') == tx_input.prev_txid and utxo.get('vout') == tx_input.output_n:
                        input_sum += utxo.get('value', 0)
                        utxo_found = True
                        break
                
                if not utxo_found:
                    issues.append(f"UTXO não encontrado: {tx_input.prev_txid}:{tx_input.output_n}")
            else:
                if hasattr(tx_input, 'value') and tx_input.value:
                    input_sum += tx_input.value
                else:
                    issues.append(f"Input {i} não tem valor definido e endereço não disponível")
        
        if input_sum == 0:
            return False, ["Não foi possível verificar os valores dos inputs"], 0, output_sum
        
        has_sufficient_funds = input_sum >= output_sum
        
        if not has_sufficient_funds:
            issues.append(f"Inputs ({input_sum}) menores que outputs ({output_sum})")
        
        return has_sufficient_funds, issues, input_sum, output_sum
    
    except Exception as e:
        logger.error(f"Erro ao validar fundos: {str(e)}", exc_info=True)
        issues.append(f"Erro na validação de fundos: {str(e)}")
        return False, issues, input_sum, output_sum 