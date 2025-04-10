from pydantic import BaseModel, Field
from typing import Optional

class SignRequest(BaseModel):
    tx_hex: str = Field(..., description="Transação não assinada em formato hexadecimal")
    private_key: str = Field(..., description="Chave privada em formato WIF ou hexadecimal")
    network: Optional[str] = Field(None, description="Rede Bitcoin (mainnet ou testnet)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tx_hex": "0200000001fd885a6a456f5a11d1c417cd8c6a8ba9d355d1e16d7c137a60fece8e8c13793",
                    "private_key": "cVbZ9eQyCQKionG7J7xu5VLcKQzoubd6uv9pkzmfP24vRkXdLYGN",
                    "network": "testnet"
                }
            ]
        }
    }

class SignResponse(BaseModel):
    tx_hex: str = Field(..., description="Transação assinada em formato hexadecimal")
    txid: str = Field(..., description="ID da transação (hash da transação)")
    is_signed: bool = Field(..., description="Indica se a transação foi assinada com sucesso")
    signatures_count: int = Field(..., description="Número de assinaturas adicionadas")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tx_hex": "0200000000010154f5a67cb14d7e50056f53263b72998c35e2f2acdbbe453d52c3b46c8e16a6fe0000000000ffffffff01905f010000000000160014fd0c0f798a94620c260889b3fff0b7dbd445e0b502483045022100f4e9bfc91f0cd516d65c4b4d001699a1272c9e274cde3bda9c1292178d3dcfc2022009be6ced0fc4eae664174d508a04933a4a7e6687947aae0a4d0848bcedbf743601210316de23a6c2dac233daddabc8de3f1bbd801da4171b09915cfc78e2354ebe6e9900000000",
                    "txid": "a1b2c3d4e5f67e8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f67e8a9b0c1d2e3",
                    "is_signed": True,
                    "signatures_count": 1
                }
            ]
        }
    }
