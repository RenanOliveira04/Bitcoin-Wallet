from pydantic import BaseModel, Field
from typing import Optional

class KeyRequest(BaseModel):
    method: str = Field(..., description="Método de geração: 'entropy', 'bip39' ou 'bip32'")
    mnemonic: Optional[str] = Field(None, description="Frase mnemônica (opcional - será gerada se não fornecida)")
    derivation_path: Optional[str] = Field("m/44'/1'/0'/0/0", description="Caminho de derivação BIP32")
    network: str = "testnet"
    password: Optional[str] = None

class KeyResponse(BaseModel):
    private_key: str
    public_key: str
    address: str
    derivation_path: Optional[str] = None
    mnemonic: Optional[str] = None