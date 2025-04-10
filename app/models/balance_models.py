from pydantic import BaseModel
from typing import List

class UTXOModel(BaseModel):
    txid: str
    vout: int
    value: int
    script: str
    confirmations: int
    address: str

class BalanceModel(BaseModel):
    balance: int
    utxos: List[UTXOModel]
