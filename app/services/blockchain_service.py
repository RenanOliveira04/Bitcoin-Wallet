import requests
from app.dependencies import get_blockchain_api_url

def get_balance(address: str, network: str) -> dict:
    url = f"{get_blockchain_api_url(network)}/address/{address}/balance"
    response = requests.get(url)
    return response.json()

def get_utxos(address: str, network: str) -> list:
    url = f"{get_blockchain_api_url(network)}/address/{address}/utxo"
    response = requests.get(url)
    return response.json()