from pydantic import BaseModel, Field
from typing import Optional, Literal
from app.dependencies import get_network

class KeyRequest(BaseModel):
    method: str = Field(..., description="Método de geração de chaves: 'entropy', 'bip39' ou 'bip32'")
    mnemonic: Optional[str] = Field(None, description="Frase mnemônica (opcional - será gerada se não fornecida)")
    derivation_path: Optional[str] = Field("m/44'/1'/0'/0/0", description="Caminho de derivação BIP32")
    network: str = Field(default_factory=get_network, description="Rede Bitcoin (mainnet ou testnet)")
    password: Optional[str] = Field(None, description="Senha opcional para derivação da chave")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "method": "entropy",
                    "network": "testnet"
                },
                {
                    "method": "bip39",
                    "mnemonic": "glass excess betray build gun intact calm calm broccoli disease calm voice",
                    "network": "testnet"
                },
                {
                    "method": "bip32",
                    "derivation_path": "m/84'/1'/0'/0/0",
                    "mnemonic": "glass excess betray build gun intact calm calm broccoli disease calm voice",
                    "network": "testnet",
                    "password": "senha_opcional"
                }
            ]
        }
    }

class KeyResponse(BaseModel):
    private_key: str
    public_key: str
    address: str  # Endereço no formato padrão P2PKH para compatibilidade
    network: str
    derivation_path: Optional[str] = None
    mnemonic: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "private_key": "cVbZ9eQyCQKionG7J7xu5VLcKQzoubd6uv9pkzmfP24vRkXdLYGN",
                    "public_key": "03a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8d",
                    "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2",
                    "network": "testnet",
                    "derivation_path": "m/44'/1'/0'/0/0",
                    "mnemonic": "glass excess betray build gun intact calm calm broccoli disease calm voice"
                }
            ]
        }
    }