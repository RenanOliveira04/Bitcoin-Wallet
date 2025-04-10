from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class ValidateRequest(BaseModel):
    tx_hex: str = Field(..., description="Transação Bitcoin em formato hexadecimal")
    network: Optional[str] = Field(None, description="Rede Bitcoin (mainnet ou testnet)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tx_hex": "0200000001fd885a6a456f5a11d1c417cd8c6a8ba9d355d1e16d7c137a60fece8e8c13793",
                    "network": "testnet"
                }
            ]
        }
    }

class ValidateResponse(BaseModel):
    is_valid: bool = Field(..., description="Indica se a transação é válida")
    details: Dict = Field(..., description="Detalhes da transação validada")
    issues: Optional[List[str]] = Field(None, description="Lista de problemas encontrados (se houver)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "is_valid": True,
                    "details": {
                        "version": 2,
                        "locktime": 0,
                        "inputs_count": 1,
                        "outputs_count": 2,
                        "total_input": 50000,
                        "total_output": 49000,
                        "fee": 1000,
                        "is_signed": True,
                        "estimated_size": 225,
                        "estimated_fee_rate": 4.44
                    }
                },
                {
                    "is_valid": False,
                    "issues": [
                        "Entrada insuficiente para cobrir saída: faltam 5000 satoshis",
                        "Assinatura inválida na entrada 0"
                    ],
                    "details": {
                        "version": 2,
                        "inputs_count": 1,
                        "outputs_count": 1,
                        "total_input": 10000,
                        "total_output": 15000,
                        "fee": -5000,
                        "is_signed": True
                    }
                }
            ]
        }
    }
