from pydantic import BaseModel, Field
from typing import Optional, Literal
from app.dependencies import get_network, get_default_key_type

class KeyRequest(BaseModel):
    method: str = Field(..., description="Método de geração: 'entropy', 'bip39' ou 'bip32'")
    mnemonic: Optional[str] = Field(None, description="Frase mnemônica (opcional - será gerada se não fornecida)")
    derivation_path: Optional[str] = Field("m/44'/1'/0'/0/0", description="Caminho de derivação BIP32")
    network: str = Field(default_factory=get_network, description="Rede Bitcoin (mainnet ou testnet)")
    key_format: str = Field(default_factory=get_default_key_type, description="Formato do endereço (p2pkh, p2sh, p2wpkh, p2tr)")
    password: Optional[str] = Field(None, description="Senha opcional para derivação da chave")

class KeyResponse(BaseModel):
    private_key: str
    public_key: str
    address: str
    format: str
    network: str
    derivation_path: Optional[str] = None
    mnemonic: Optional[str] = None