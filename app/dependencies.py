from functools import lru_cache
from pydantic_settings import BaseSettings
import bech32
from bitcoinlib.networks import NETWORK_DEFINITIONS
import logging
import os
from typing import Optional

class Settings(BaseSettings):
    # Configurações básicas com valores padrão não sensíveis
    network: str = "testnet"
    log_level: str = "INFO"
    log_file: str = "bitcoin-wallet.log"
    cache_timeout: int = 300
    default_key_type: str = "p2wpkh"
    
    # Configurações sensíveis sem valores padrão
    blockchain_api_url: Optional[str] = None
    mempool_api_url: Optional[str] = None
    
    # Configurações secretas (podem ser adicionadas no futuro)
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Esconder configurações sensíveis na saída dos logs e representação de string
        secrets = ["blockchain_api_url", "mempool_api_url", "api_key", "api_secret"]

# Não é necessário adicionar redes manualmente, apenas fazer o mapeamento correto
# A biblioteca já possui "bitcoin" que é equivalente a "mainnet"

@lru_cache
def get_settings():
    # Iniciar com valores padrão seguros
    settings = Settings()
    
    # Definir URLs padrão apenas se não estiverem definidas no .env
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
    # Corrigir mapeamento de rede para prefixo HRP correto
    network_to_hrp = {
        "mainnet": "bc",
        "bitcoin": "bc",
        "testnet": "tb",
        "regtest": "bcrt"
    }
    
    hrp = network_to_hrp.get(network, "tb")
    converted = bech32.convertbits(data, 8, 5)
    return bech32.bech32_encode(hrp, [witver] + converted)

def get_blockchain_api_url(network: str = None):
    if not network:
        network = get_network()
    # Corrigir mapeamento de nomes de rede
    if network == "mainnet":
        network = "bitcoin"
    return f"{get_settings().blockchain_api_url}/{network}"

def get_mempool_api_url(network: str = None):
    if not network:
        network = get_network()
    
    base_url = get_settings().mempool_api_url
    
    # Ajusta URL para testnet, se necessário
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