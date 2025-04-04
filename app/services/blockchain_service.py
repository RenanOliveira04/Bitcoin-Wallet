import requests
from app.dependencies import get_blockchain_api_url
from fastapi import HTTPException
import logging
import json

logger = logging.getLogger(__name__)

def get_balance(address: str, network: str) -> dict:
    try:
        logger.info(f"Consultando saldo para o endereço {address} na rede {network}")
        
        if network == "testnet":
            # Para testnet, usamos uma API específica (blockstream.info)
            url = f"https://blockstream.info/testnet/api/address/{address}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Transformar para o formato padrão
            return {
                "confirmed": data.get("chain_stats", {}).get("funded_txo_sum", 0) - data.get("chain_stats", {}).get("spent_txo_sum", 0),
                "unconfirmed": data.get("mempool_stats", {}).get("funded_txo_sum", 0) - data.get("mempool_stats", {}).get("spent_txo_sum", 0)
            }
        else:
            # Para mainnet, usamos a API original
            url = f"{get_blockchain_api_url(network)}/address/{address}/balance"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao consultar saldo: {str(e)}")
        
        # Retornar dados simulados para fins de demonstração
        dummy_data = {"confirmed": 0, "unconfirmed": 0}
        logger.warning(f"Retornando dados simulados: {dummy_data}")
        return dummy_data

def get_utxos(address: str, network: str) -> list:
    try:
        logger.info(f"Consultando UTXOs para o endereço {address} na rede {network}")
        
        if network == "testnet":
            # Para testnet, usamos uma API específica (blockstream.info)
            url = f"https://blockstream.info/testnet/api/address/{address}/utxo"
            response = requests.get(url)
            response.raise_for_status()
            utxos = response.json()
            
            # Transformar para o formato padrão
            result = []
            for utxo in utxos:
                result.append({
                    "txid": utxo.get("txid"),
                    "vout": utxo.get("vout"),
                    "value": utxo.get("value"),
                    "status": {
                        "confirmed": True,
                        "block_height": utxo.get("status", {}).get("block_height")
                    }
                })
            return result
        else:
            # Para mainnet, usamos a API original
            url = f"{get_blockchain_api_url(network)}/address/{address}/utxo"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao consultar UTXOs: {str(e)}")
        
        # Retornar dados simulados para fins de demonstração
        dummy_data = []
        logger.warning(f"Retornando dados simulados: {dummy_data}")
        return dummy_data