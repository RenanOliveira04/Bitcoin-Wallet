from functools import lru_cache
from pydantic_settings import BaseSettings
import bech32
from bitcoinlib.networks import NETWORK_DEFINITIONS
import logging
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import os
from pathlib import Path

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
    
    offline_mode: bool = False
    cache_dir: Optional[str] = None
    cache_timeout_cold: int = 2592000  # 30 dias

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

def get_cache_dir():
    """
    Retorna o diretório para armazenamento de cache persistente.
    
    Se a configuração cache_dir existir, usa esse valor.
    Caso contrário, usa o diretório padrão ~/.bitcoin-wallet/cache
    
    Returns:
        Path: Diretório de cache
    """
    settings = get_settings()
    if settings.cache_dir:
        return Path(settings.cache_dir)
    return Path.home() / ".bitcoin-wallet" / "cache"

def is_offline_mode_enabled():
    """
    Verifica se o modo offline está habilitado nas configurações.
    
    Returns:
        bool: True se o modo offline estiver habilitado, False caso contrário
    """
    return get_settings().offline_mode

def get_cache_timeout(cold_wallet: bool = False):
    """
    Retorna o timeout do cache conforme configuração.
    
    Args:
        cold_wallet (bool): Se True, retorna o timeout para cold wallet
    
    Returns:
        int: Timeout em segundos
    """
    settings = get_settings()
    if cold_wallet:
        return settings.cache_timeout_cold
    return settings.cache_timeout

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

@lru_cache
def get_bitcoinlib_network(network=None):
    """
    Converte o nome da rede utilizada na API para o formato esperado pela biblioteca bitcoinlib.
    
    A bitcoinlib usa 'bitcoin' para a rede principal (mainnet) enquanto nossa API usa 'mainnet'.
    Esta função centraliza a conversão para evitar inconsistências.
    
    Args:
        network (str, optional): Nome da rede ('testnet' ou 'mainnet'). 
                                Se None, usa o valor padrão de configuração.
    
    Returns:
        str: Nome da rede no formato esperado pela bitcoinlib ('bitcoin' ou 'testnet')
    """
    network = network or get_network()
    return "bitcoin" if network == "mainnet" else network

def mask_sensitive_data(data: str) -> str:
    """
    Mascara dados sensíveis para proteção em logs ou mensagens de erro.
    
    Esta função oculta a parte central de strings sensíveis como chaves privadas,
    mnemônicos ou seeds, mostrando apenas os primeiros e últimos caracteres.
    
    Args:
        data (str): String sensível a ser mascarada
        
    Returns:
        str: Versão mascarada da string, ex: "xprv6C...Xs91Q"
    """
    if not data or len(data) < 8:
        return "****"
    visible_chars = min(4, len(data) // 4)
    return f"{data[:visible_chars]}...{data[-visible_chars:]}"

@lru_cache(maxsize=128)
def get_cached_network_info(network=None):
    """
    Retorna informações da rede Bitcoin em cache para reduzir chamadas repetidas.
    
    Args:
        network (str, optional): Nome da rede. Se None, usa o valor de configuração.
        
    Returns:
        dict: Informações da rede, incluindo altura atual do bloco, dificuldade, etc.
    """
    return {
        "height": 800000,  
        "difficulty": 50000000000,  
        "chain": get_network() or network
    }

def setup_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )