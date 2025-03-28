from functools import lru_cache
from pydantic_settings import BaseSettings

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

def get_blockchain_api_url(network: str = None):
    if not network:
        network = get_network()
    return f"{get_settings().blockchain_api_url}/{network}"