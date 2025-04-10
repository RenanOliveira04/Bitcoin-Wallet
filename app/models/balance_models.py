from pydantic import BaseModel, Field
from typing import List

class UTXOModel(BaseModel):
    txid: str = Field(..., description="ID da transação que contém o UTXO")
    vout: int = Field(..., description="Índice da saída na transação")
    value: int = Field(..., description="Valor em satoshis")
    script: str = Field(..., description="Script de bloqueio em formato hexadecimal")
    confirmations: int = Field(..., description="Número de confirmações")
    address: str = Field(..., description="Endereço associado ao UTXO")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                    "vout": 0,
                    "value": 50000,
                    "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                    "confirmations": 6,
                    "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2"
                }
            ]
        }
    }

class BalanceModel(BaseModel):
    balance: int = Field(..., description="Saldo total disponível em satoshis")
    utxos: List[UTXOModel] = Field(..., description="Lista de UTXOs disponíveis")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "balance": 150000,
                    "utxos": [
                        {
                            "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                            "vout": 0,
                            "value": 50000,
                            "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                            "confirmations": 6,
                            "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2"
                        },
                        {
                            "txid": "8b9ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d284f",
                            "vout": 1,
                            "value": 100000,
                            "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                            "confirmations": 3,
                            "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2"
                        }
                    ]
                }
            ]
        }
    }
