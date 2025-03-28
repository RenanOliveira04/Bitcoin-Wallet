from pydantic import BaseModel
from typing import List, Dict, Optional

class TransactionRequest(BaseModel):
    inputs: List[Dict[str, str]]  # [{"txid": "...", "vout": 0}]
    outputs: List[Dict[str, str]]  # [{"address": "...", "value": "..."}]
    fee_rate: Optional[float] = None  # sat/vbyte

class TransactionResponse(BaseModel):
    raw_transaction: str
    txid: str
    fee: Optional[float] = None