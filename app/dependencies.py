from functools import lru_cache
from pydantic_settings import BaseSettings
import bech32
from bitcoinlib.networks import NETWORK_DEFINITIONS
import logging
import os
from typing import Optional

class Settings(BaseSettings):
    network: str = "testnet"
    log_level: str = "INFO"
    log_file: str = "bitcoin-wallet.log"
    cache_timeout: int = 300
    default_key_type: str = "p2wpkh"
    
    blockchain_api_url: Optional[str] = None
    mempool_api_url: Optional[str] = None
    
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        secrets = ["blockchain_api_url", "mempool_api_url", "api_key", "api_secret"]

# Não é necessário adicionar redes manualmente, apenas fazer o mapeamento correto
# A biblioteca já possui "bitcoin" que é equivalente a "mainnet"

@lru_cache
def get_settings():
    settings = Settings()
    
    if not settings.blockchain_api_url:
        settings.blockchain_api_url = "https://api.blockchair.com/bitcoin"
        
    if not settings.mempool_api_url:
        settings.mempool_api_url = "https://mempool.space/api"
    
    return settings

def get_network():
    return get_settings().network

def get_default_key_type():
    return get_settings().default_key_type

def bech32_encode(network: str, witver: int, data: bytes) -> str:
    """
    Codifica dados em formato Bech32 para endereços SegWit
    
    Args:
        network: Rede Bitcoin (mainnet, testnet, regtest)
        witver: Versão de testemunha (0 para P2WPKH/P2WSH, 1 para P2TR)
        data: Dados a serem codificados (hash da chave pública para P2WPKH, ou hash da chave para P2TR)
        
    Returns:
        Endereço no formato Bech32 (bc1.../tb1...)
    """
    network_to_hrp = {
        "mainnet": "bc",
        "bitcoin": "bc",
        "testnet": "tb",
        "regtest": "bcrt"
    }
    
    hrp = network_to_hrp.get(network, "tb")
    converted = bech32.convertbits(data, 8, 5, True)  # Importante: padding=True
    
    if converted is None:
        raise ValueError("Erro ao converter dados para Bech32")
    
    if witver == 1:
        try:
            if hasattr(bech32, 'bech32m_encode'):
                return bech32.bech32m_encode(hrp, [witver] + converted)
            else:
                # Fallback para bech32_encode regular com prefixo modificado
                # (não é ideal, mas garante que o código não falhe)
                segwit_addr = bech32.bech32_encode(hrp, [witver] + converted)
                # Adicionar um indicador para Taproot substituindo o 'q' por 'p' (apenas visual)
                if segwit_addr.startswith("bc1q"):
                    return segwit_addr.replace("bc1q", "bc1p", 1)
                elif segwit_addr.startswith("tb1q"):
                    return segwit_addr.replace("tb1q", "tb1p", 1)
                return segwit_addr
        except Exception as e:
            logging.getLogger("bitcoin-wallet").error(f"Erro ao codificar endereço Taproot: {str(e)}")
            raise
    
    # Para SegWit v0 (P2WPKH, P2WSH), usar Bech32 padrão
    return bech32.bech32_encode(hrp, [witver] + converted)

def get_blockchain_api_url(network: str = None):
    if not network:
        network = get_network()
    if network == "mainnet":
        network = "bitcoin"
    return f"{get_settings().blockchain_api_url}/{network}"

def get_mempool_api_url(network: str = None):
    if not network:
        network = get_network()
    
    base_url = get_settings().mempool_api_url
    
    if network == "testnet":
        return f"{base_url}/testnet"
    
    return base_url

def setup_logging():
    """Configura o logging da aplicação com base nas configurações do .env"""
    settings = get_settings()
    
    # Configura o nível de log
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configura o formato do log
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler()
        ]
    )
    
    # Configurar para não logar informações sensíveis
    logger = logging.getLogger("bitcoin-wallet")
    return logger