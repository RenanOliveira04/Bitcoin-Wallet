from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from bitcoinlib.transactions import Transaction
def is_hex(s: str) -> bool:
    """Check if a string is a valid hexadecimal string."""
    try:
        int(s, 16)
        return True
    except (ValueError, TypeError):
        return False
from decimal import Decimal
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"

class ValidationIssue(BaseModel):
    """Represents a validation issue with severity and details"""
    code: str
    message: str
    severity: str = "error"  # error, warning, info
    field: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

class TransactionValidationResult(BaseModel):
    """Result of transaction validation with detailed information"""
    is_valid: bool = Field(..., description="Overall validation result")
    status: ValidationStatus = Field(..., description="Validation status")
    details: Dict[str, Any] = Field(default_factory=dict, description="Validation details")
    issues: List[ValidationIssue] = Field(default_factory=list, description="List of validation issues")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

class TransactionValidator:
    """Service for validating Bitcoin transactions with comprehensive checks"""
    
    def __init__(self, network: str = "testnet"):
        self.network = network
        self.min_fee_rate = 1  # sat/byte
        self.max_fee_rate = 1000  # sat/byte
        self.dust_threshold = 546  # satoshis
        self.max_transaction_size = 400_000  # bytes
        self.max_script_size = 10_000  # bytes

    def validate_transaction(self, tx_hex: str) -> TransactionValidationResult:
        """
        Validate a Bitcoin transaction with comprehensive checks.
        
        Args:
            tx_hex: Transaction in hexadecimal format
            
        Returns:
            TransactionValidationResult: Detailed validation result
        """
        result = TransactionValidationResult(
            is_valid=False,
            status=ValidationStatus.PENDING,
            details={}
        )
        
        try:
            if not is_hex(tx_hex):
                self._add_issue(result, "invalid_hex", "Invalid hexadecimal format")
                return self._finalize_validation(result)
                
            if len(tx_hex) < 20:  
                self._add_issue(result, "tx_too_short", "Transaction hex is too short")
                return self._finalize_validation(result)
                
            try:
                tx = Transaction.parse_hex(tx_hex)
                result.details.update({
                    "txid": tx.txid,
                    "version": tx.version,
                    "locktime": getattr(tx, 'locktime', 0),
                    "size": getattr(tx, 'size', 0),
                    "vsize": getattr(tx, 'vsize', 0),
                    "weight": getattr(tx, 'weight', 0),
                })
            except Exception as e:
                self._add_issue(
                    result, 
                    "parse_error", 
                    f"Failed to parse transaction: {str(e)}"
                )
                return self._finalize_validation(result)
                
            self._validate_structure(tx, result)
            if not result.is_valid:
                return self._finalize_validation(result)
                
            self._validate_inputs(tx, result)
            self._validate_outputs(tx, result)
            
            self._validate_fees_and_balance(tx, result)
            
            if any(inp.script_sig for inp in tx.inputs if hasattr(inp, 'script_sig')):
                self._validate_signatures(tx, result)
            
            return self._finalize_validation(result)
            
        except Exception as e:
            logger.error(f"Unexpected error during validation: {str(e)}", exc_info=True)
            self._add_issue(
                result,
                "validation_error",
                f"Unexpected error during validation: {str(e)}",
                severity="critical"
            )
            return self._finalize_validation(result)

    def _validate_structure(self, tx: Transaction, result: TransactionValidationResult) -> None:
        """Validate basic transaction structure"""
        if not tx.inputs:
            self._add_issue(result, "no_inputs", "Transaction has no inputs")
            
        if not tx.outputs:
            self._add_issue(result, "no_outputs", "Transaction has no outputs")
            
        if len(tx.inputs) > 10_000:  
            self._add_issue(
                result,
                "too_many_inputs",
                f"Transaction has too many inputs: {len(tx.inputs)}",
                severity="warning"
            )
            
        if len(tx.outputs) > 10_000:  
            self._add_issue(
                result,
                "too_many_outputs",
                f"Transaction has too many outputs: {len(tx.outputs)}",
                severity="warning"
            )
            
        tx_size = getattr(tx, 'size', 0)
        if tx_size > self.max_transaction_size:
            self._add_issue(
                result,
                "tx_too_large",
                f"Transaction size {tx_size} bytes exceeds maximum {self.max_transaction_size} bytes"
            )

    def _validate_inputs(self, tx: Transaction, result: TransactionValidationResult) -> None:
        """Validate transaction inputs"""
        input_sum = 0
        for i, tx_input in enumerate(tx.inputs):
            if not hasattr(tx_input, 'prev_txid') or not tx_input.prev_txid:
                self._add_issue(
                    result,
                    f"input_{i}_missing_txid",
                    f"Input {i} is missing previous transaction ID",
                    field=f"inputs[{i}].prev_txid"
                )
                continue
                
            if hasattr(tx_input, 'script_sig') and len(tx_input.script_sig) > self.max_script_size:
                self._add_issue(
                    result,
                    f"input_{i}_script_too_large",
                    f"Input {i} script is too large",
                    field=f"inputs[{i}].script_sig",
                    severity="warning"
                )
            
            if hasattr(tx_input, 'address') and tx_input.address:
                utxos = get_utxos(tx_input.address, self.network)
                utxo = next(
                    (u for u in utxos 
                     if u.get('txid') == tx_input.prev_txid and 
                        u.get('vout') == getattr(tx_input, 'output_n', -1)),
                    None
                )
                
                if utxo:
                    input_sum += Decimal(str(utxo.get('value', 0)))
                else:
                    self._add_issue(
                        result,
                        f"input_{i}_utxo_not_found",
                        f"UTXO not found for input {i}",
                        details={
                            "txid": tx_input.prev_txid,
                            "vout": getattr(tx_input, 'output_n', None),
                            "address": tx_input.address
                        }
                    )
            elif hasattr(tx_input, 'value') and tx_input.value:
                input_sum += Decimal(str(tx_input.value))
            else:
                self._add_issue(
                    result,
                    f"input_{i}_no_value",
                    f"Input {i} has no value and no address to look up UTXO",
                    field=f"inputs[{i}].value"
                )
        
        result.details["input_sum"] = float(input_sum)
        result.details["input_count"] = len(tx.inputs)

    def _validate_outputs(self, tx: Transaction, result: TransactionValidationResult) -> None:
        """Validate transaction outputs"""
        output_sum = Decimal(0)
        for i, output in enumerate(tx.outputs):
            output_value = Decimal(str(output.value))
            output_sum += output_value
            
            if output_value < self.dust_threshold:
                self._add_issue(
                    result,
                    f"output_{i}_dust",
                    f"Output {i} value {output_value} is below dust threshold",
                    field=f"outputs[{i}].value",
                    severity="warning"
                )
            
            if hasattr(output, 'script') and len(output.script) > self.max_script_size:
                self._add_issue(
                    result,
                    f"output_{i}_script_too_large",
                    f"Output {i} script is too large",
                    field=f"outputs[{i}].script",
                    severity="warning"
                )
        
        result.details["output_sum"] = float(output_sum)
        result.details["output_count"] = len(tx.outputs)

    def _validate_fees_and_balance(self, tx: Transaction, result: TransactionValidationResult) -> None:
        """Validate transaction fees and input/output balance"""
        input_sum = Decimal(str(result.details.get("input_sum", 0)))
        output_sum = Decimal(str(result.details.get("output_sum", 0)))
        
        if input_sum < output_sum:
            self._add_issue(
                result,
                "insufficient_funds",
                f"Insufficient input amount: {input_sum} < {output_sum}",
                details={
                    "input_sum": float(input_sum),
                    "output_sum": float(output_sum),
                    "deficit": float(output_sum - input_sum)
                }
            )
            return
            
        fee = input_sum - output_sum
        result.details["fee"] = float(fee)
        
        tx_size = getattr(tx, 'size', 0)
        if tx_size > 0:
            fee_rate = fee / tx_size
            result.details["fee_rate"] = float(fee_rate)
            
            if fee_rate < self.min_fee_rate:
                self._add_issue(
                    result,
                    "fee_too_low",
                    f"Fee rate {fee_rate:.2f} sat/byte is below minimum {self.min_fee_rate}",
                    severity="warning"
                )
            elif fee_rate > self.max_fee_rate:
                self._add_issue(
                    result,
                    "fee_too_high",
                    f"Fee rate {fee_rate:.2f} sat/byte is above maximum {self.max_fee_rate}",
                    severity="warning"
                )

    def _validate_signatures(self, tx: Transaction, result: TransactionValidationResult) -> None:
        """Validate transaction signatures"""
        for i, tx_input in enumerate(tx.inputs):
            if not hasattr(tx_input, 'script_sig') or not tx_input.script_sig:
                continue
                
            try:
                if hasattr(tx_input, 'verify'):
                    if not tx_input.verify():
                        self._add_issue(
                            result,
                            f"input_{i}_invalid_signature",
                            f"Invalid signature for input {i}",
                            field=f"inputs[{i}].script_sig"
                        )
            except Exception as e:
                self._add_issue(
                    result,
                    f"input_{i}_signature_error",
                    f"Error verifying signature for input {i}: {str(e)}",
                    details={"error": str(e)}
                )

    def _add_issue(
        self,
        result: TransactionValidationResult,
        code: str,
        message: str,
        severity: str = "error",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a validation issue to the result"""
        issue = ValidationIssue(
            code=code,
            message=message,
            severity=severity,
            field=field,
            details=details or {}
        )
        result.issues.append(issue)

    def _finalize_validation(self, result: TransactionValidationResult) -> TransactionValidationResult:
        """Finalize the validation result"""
        result.is_valid = all(
            issue.severity not in ["error", "critical"]
            for issue in result.issues
        )
        
        if any(issue.severity == "critical" for issue in result.issues):
            result.status = ValidationStatus.INVALID
        elif any(issue.severity == "error" for issue in result.issues):
            result.status = ValidationStatus.INVALID
        else:
            result.status = ValidationStatus.VALID if result.is_valid else ValidationStatus.PENDING
        
        return result

transaction_validator = TransactionValidator()

def validate_transaction(tx_hex: str, network: str = "testnet") -> TransactionValidationResult:
    """
    Validate a Bitcoin transaction.
    
    Args:
        tx_hex: Transaction in hexadecimal format
        network: Bitcoin network ('mainnet' or 'testnet')
        
    Returns:
        TransactionValidationResult: Validation result with details
    """
    if not tx_hex or not isinstance(tx_hex, str):
        raise ValueError("Transaction hex must be a non-empty string")
        
    validator = TransactionValidator(network=network)
    return validator.validate_transaction(tx_hex)