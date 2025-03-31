from functools import lru_cache
from pydantic_settings import BaseSettings
import bech32

class Settings(BaseSettings):
    network: str = "testnet"
    blockchain_api_url: str = "https://api.blockchair.com/bitcoin"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()

def get_network():
    return get_settings().network

def bech32_encode(network: str, witver: int, data: bytes) -> str:
    hrp = "bc" if network == "mainnet" else "tb"
    converted = bech32.convertbits(data, 8, 5)
    return bech32.bech32_encode(hrp, [witver] + converted)

def get_blockchain_api_url(network: str = None):
    if not network:
        network = get_network()
    return f"{get_settings().blockchain_api_url}/{network}"