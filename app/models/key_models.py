from pydantic import BaseModel, Field
from typing import Optional
from app.dependencies import get_network
from enum import Enum

class KeyMethod(str, Enum):
    entropy = "entropy"
    bip39 = "bip39"
    bip32 = "bip32"

class KeyFormat(str, Enum):
    p2pkh = "p2pkh"
    p2sh = "p2sh"
    p2wpkh = "p2wpkh"
    p2tr = "p2tr"

class Network(str, Enum):
    testnet = "testnet"
    mainnet = "mainnet"

class KeyRequest(BaseModel):
    method: KeyMethod = Field(
        default="entropy",
        description="Método de geração da chave: 'entropy' (aleatória), 'bip39' (mnemônico), 'bip32' (derivação)."
    )
    network: Network = Field(
        default="testnet",
        description="Rede Bitcoin: 'testnet' (para testes) ou 'mainnet' (produção)."
    )
    mnemonic: Optional[str] = Field(
        None,
        description="Frase mnemônica para recuperação (somente para método 'bip39' ou 'bip32')."
    )
    derivation_path: Optional[str] = Field(
        None,
        description="Caminho de derivação BIP32 (somente para método 'bip32')."
    )
    passphrase: Optional[str] = Field(
        None,
        description="Senha opcional para adicionar entropia adicional."
    )
    key_format: Optional[KeyFormat] = Field(
        None,
        description="Formato da chave e endereço: 'p2pkh', 'p2sh', 'p2wpkh', 'p2tr'."
    )
    
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
                    "passphrase": "senha_opcional"
                }
            ]
        }
    }

class KeyResponse(BaseModel):
    private_key: str = Field(..., description="Chave privada em formato WIF ou hexadecimal")
    public_key: str = Field(..., description="Chave pública em formato hexadecimal")
    address: str = Field(..., description="Endereço Bitcoin gerado")
    format: KeyFormat = Field(..., description="Formato do endereço gerado")
    network: Network = Field(..., description="Rede utilizada (testnet ou mainnet)")
    derivation_path: Optional[str] = Field(None, description="Caminho de derivação utilizado (para BIP32)")
    mnemonic: Optional[str] = Field(None, description="Frase mnemônica (para BIP39 ou BIP32)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "private_key": "cVbZ9eQyCQKionG7J7xu5VLcKQzoubd6uv9pkzmfP24vRkXdLYGN",
                    "public_key": "03a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8d",
                    "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2",
                    "format": "p2pkh",
                    "network": "testnet",
                    "derivation_path": "m/44'/1'/0'/0/0",
                    "mnemonic": "glass excess betray build gun intact calm calm broccoli disease calm voice"
                }
            ]
        }
    }