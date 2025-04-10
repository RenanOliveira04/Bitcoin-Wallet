from pydantic import BaseModel, Field

class BroadcastRequest(BaseModel):
    tx_hex: str = Field(..., description="Transação assinada em formato hexadecimal")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tx_hex": "0200000000010154f5a67cb14d7e50056f53263b72998c35e2f2acdbbe453d52c3b46c8e16a6fe0000000000ffffffff01905f010000000000160014fd0c0f798a94620c260889b3fff0b7dbd445e0b502483045022100f4e9bfc91f0cd516d65c4b4d001699a1272c9e274cde3bda9c1292178d3dcfc2022009be6ced0fc4eae664174d508a04933a4a7e6687947aae0a4d0848bcedbf743601210316de23a6c2dac233daddabc8de3f1bbd801da4171b09915cfc78e2354ebe6e9900000000"
                }
            ]
        }
    }

class BroadcastResponse(BaseModel):
    txid: str = Field(..., description="ID da transação (hash da transação)")
    status: str = Field(..., description="Status da transmissão (sent, rejected, etc)")
    explorer_url: str = Field(..., description="URL para visualizar a transação em um explorador de blockchain")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                    "status": "sent",
                    "explorer_url": "https://blockstream.info/testnet/tx/7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e"
                }
            ]
        }
    }
