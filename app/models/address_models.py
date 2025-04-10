from enum import Enum
from pydantic import BaseModel, Field

class AddressFormat(str, Enum):
    p2pkh = "p2pkh"
    p2sh = "p2sh"
    p2wpkh = "p2wpkh"
    p2tr = "p2tr"

class AddressResponse(BaseModel):
    address: str = Field(..., description="Endereço Bitcoin gerado")
    format: AddressFormat = Field(..., description="Formato do endereço (p2pkh, p2sh, p2wpkh, p2tr)")
    network: str = Field(..., description="Rede Bitcoin (testnet ou mainnet)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2",
                    "format": "p2pkh",
                    "network": "testnet"
                },
                {
                    "address": "2N7SPBUArsbhbzGxzGXLiFc36T3MdFEwdZV",
                    "format": "p2sh",
                    "network": "testnet"
                },
                {
                    "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                    "format": "p2wpkh",
                    "network": "testnet"
                },
                {
                    "address": "tb1p6h5fuzmnvpdthf5shf0qqjzwy7wsqc5rhmgq2ks9xrak4ry6mtrscsqvzp",
                    "format": "p2tr",
                    "network": "testnet"
                }
            ]
        }
    }