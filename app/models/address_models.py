from enum import Enum
from pydantic import BaseModel

class AddressFormat(str, Enum):
    p2pkh = "p2pkh"
    p2sh = "p2sh"
    p2wpkh = "p2wpkh"
    p2tr = "p2tr"

class AddressResponse(BaseModel):
    address: str
    format: AddressFormat
    network: str