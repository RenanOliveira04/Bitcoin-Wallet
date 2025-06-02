from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class WalletCreate(BaseModel):
    """Model for creating a new wallet"""
    name: str = Field(..., description="Nome da carteira")
    description: Optional[str] = Field(None, description="Descrição opcional da carteira")
    address: str = Field(..., description="Endereço Bitcoin")
    private_key: Optional[str] = Field(None, description="Chave privada (opcional, para carteiras watch-only)")
    public_key: str = Field(..., description="Chave pública")
    key_type: str = Field(..., description="Tipo de chave/endereço (p2pkh, p2sh, p2wpkh, p2wsh, p2tr)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Carteira de Teste",
                    "description": "Carteira para testes na rede testnet",
                    "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                    "private_key": None,  # Watch-only wallet
                    "public_key": "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
                    "key_type": "p2wpkh"
                }
            ]
        }
    }

class WalletResponse(BaseModel):
    """Model for wallet data returned by the API"""
    id: int = Field(..., description="ID da carteira")
    name: str = Field(..., description="Nome da carteira")
    description: Optional[str] = Field(None, description="Descrição opcional da carteira")
    address: str = Field(..., description="Endereço Bitcoin")
    private_key: Optional[str] = Field(None, description="Chave privada (presente apenas em carteiras completas)")
    public_key: str = Field(..., description="Chave pública")
    key_type: str = Field(..., description="Tipo de chave/endereço (p2pkh, p2sh, p2wpkh, p2wsh, p2tr)")
    network: str = Field("testnet", description="Rede (testnet)")
    created_at: Optional[str] = Field(None, description="Data de criação da carteira")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "Carteira de Teste",
                    "description": "Carteira para testes na rede testnet",
                    "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                    "private_key": None,  
                    "public_key": "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
                    "key_type": "p2wpkh",
                    "network": "testnet",
                    "created_at": "2023-10-15T10:30:00"
                }
            ]
        }
    }

class TransactionRecord(BaseModel):
    """Model for transaction records stored in the wallet database"""
    id: Optional[int] = Field(None, description="ID do registro (presente apenas em registros já salvos)")
    txid: str = Field(..., description="ID da transação")
    amount: float = Field(..., description="Valor da transação em BTC")
    fee: Optional[float] = Field(None, description="Taxa paga na transação em BTC")
    confirmations: Optional[int] = Field(0, description="Número de confirmações")
    timestamp: Optional[str] = Field(None, description="Data e hora da transação")
    status: str = Field(..., description="Status da transação (pending, confirmed, failed)")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Dados brutos da transação")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                    "amount": 0.0005,
                    "fee": 0.0001,
                    "confirmations": 6,
                    "timestamp": "2023-10-15T14:22:10",
                    "status": "confirmed",
                    "raw_data": {
                        "hex": "020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff",
                        "size": 140,
                        "weight": 560
                    }
                }
            ]
        }
    }

class UTXORecord(BaseModel):
    """Model for UTXO records stored in the wallet database"""
    id: Optional[int] = Field(None, description="ID do registro (presente apenas em registros já salvos)")
    txid: str = Field(..., description="ID da transação")
    vout: int = Field(..., description="Índice da saída na transação")
    amount: float = Field(..., description="Valor em BTC")
    script: Optional[str] = Field(None, description="Script de bloqueio em formato hexadecimal")
    confirmations: Optional[int] = Field(0, description="Número de confirmações")
    spent: bool = Field(False, description="Flag indicando se o UTXO já foi gasto")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                    "vout": 0,
                    "amount": 0.0005,
                    "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                    "confirmations": 6,
                    "spent": False
                }
            ]
        }
    }
