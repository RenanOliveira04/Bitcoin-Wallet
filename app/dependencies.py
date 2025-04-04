from functools import lru_cache
from pydantic_settings import BaseSettings
import bech32
from bitcoinlib.networks import NETWORK_DEFINITIONS

class Settings(BaseSettings):
    network: str = "testnet"
    blockchain_api_url: str = "https://api.blockchair.com/bitcoin"

    class Config:
        env_file = ".env"

# Não é necessário adicionar redes manualmente, apenas fazer o mapeamento correto
# A biblioteca já possui "bitcoin" que é equivalente a "mainnet"

@lru_cache
def get_settings():
    return Settings()

def get_network():
    return get_settings().network

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