from pydantic import BaseModel

class TransactionStatusModel(BaseModel):
    txid: str
    status: str
    confirmations: int
    block_height: int
    block_hash: str
    timestamp: str
    explorer_url: str
