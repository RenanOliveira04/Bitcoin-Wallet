from pydantic import BaseModel

class SignRequest(BaseModel):
    tx_hex: str
    private_key: str
    network: str = None

class SignResponse(BaseModel):
    tx_hex: str
    txid: str
    is_signed: bool
    signatures_count: int
