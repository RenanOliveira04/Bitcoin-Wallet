from pydantic import BaseModel

class BroadcastRequest(BaseModel):
    tx_hex: str

class BroadcastResponse(BaseModel):
    txid: str
    status: str
    explorer_url: str
