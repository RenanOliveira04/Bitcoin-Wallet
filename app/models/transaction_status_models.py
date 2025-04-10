from pydantic import BaseModel, Field
from typing import Optional

class TransactionStatusModel(BaseModel):
    txid: str = Field(..., description="ID da transação (hash da transação)")
    status: str = Field(..., description="Status atual da transação (confirmed, pending, etc)")
    confirmations: int = Field(..., description="Número de confirmações")
    block_height: Optional[int] = Field(None, description="Altura do bloco onde a transação foi incluída")
    block_hash: Optional[str] = Field(None, description="Hash do bloco onde a transação foi incluída")
    timestamp: Optional[str] = Field(None, description="Data e hora da confirmação (ISO 8601)")
    explorer_url: str = Field(..., description="URL para visualizar a transação em um explorador de blockchain")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                    "status": "confirmed",
                    "confirmations": 6,
                    "block_height": 800000,
                    "block_hash": "000000000000000000024e33c89641ef59af8bf60fdc2f32ff369b32260930ff",
                    "timestamp": "2023-04-01T12:00:00Z",
                    "explorer_url": "https://blockstream.info/testnet/tx/7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e"
                }
            ]
        }
    }
