from pydantic import BaseModel, Field
from typing import Optional, List
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

class KeyExportRequest(BaseModel):
    private_key: str = Field(..., description="Chave privada a ser exportada")
    public_key: str = Field(..., description="Chave pública a ser exportada")
    address: str = Field(..., description="Endereço Bitcoin associado às chaves")
    network: Optional[str] = Field(None, description="Rede Bitcoin (mainnet ou testnet)")
    file_format: Optional[str] = Field("txt", description="Formato do arquivo (apenas 'txt' suportado)")
    format: Optional[str] = Field(None, description="Formato do endereço (p2pkh, p2sh, p2wpkh, p2tr)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "private_key": "cPawEGNRwkFCYMJ5x5MkpJ8SQ6xFRoZpLVhKQi1bMrMHNZFmQRFz",
                    "public_key": "03a7a0c16cdf77b36dd75985a8ea6b0e3ad9c6653854f9d3d093b5a1e21e78981a",
                    "address": "mz7YZkfxRqRfL9YFLkFsUe7zVjpPEqDEUj",
                    "network": "testnet",
                    "file_format": "txt",
                    "format": "p2pkh"
                }
            ]
        }
    }

class KeyExportResponse(BaseModel):
    success: bool = Field(..., description="Indica se a exportação foi bem-sucedida")
    file_path: str = Field(..., description="Caminho completo para o arquivo gerado")
    message: str = Field(..., description="Mensagem informativa sobre a exportação")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "file_path": "/home/user/.bitcoin-wallet/keys/bitcoin_testnet_mz7YZkfx_20250415_182045.txt",
                    "message": "Chaves exportadas com sucesso para /home/user/.bitcoin-wallet/keys/bitcoin_testnet_mz7YZkfx_20250415_182045.txt"
                }
            ]
        }
    }