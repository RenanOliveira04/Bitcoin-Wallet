import requests
from app.dependencies import get_blockchain_api_url
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def get_balance(address: str, network: str) -> dict:
    """
    Consulta o saldo de um endereço Bitcoin na blockchain.
    
    Esta função recupera o saldo confirmado e não confirmado de um endereço Bitcoin
    consultando APIs blockchain externas. Para endereços testnet, utiliza o 
    blockstream.info, enquanto para endereços mainnet utiliza a API configurada
    no ambiente.
    
    ## O que são saldos confirmados e não confirmados?
    
    * **Saldo confirmado**: Representa bitcoins em transações que já foram incluídas 
      em um bloco da blockchain e tiveram pelo menos uma confirmação.
    
    * **Saldo não confirmado**: Representa bitcoins em transações que foram 
      transmitidas para a rede mas ainda não foram incluídas em um bloco
      (estão no mempool).
    
    Args:
        address (str): Endereço Bitcoin a ser consultado. Suporta todos os
            formatos de endereço (Legacy, SegWit, Native SegWit, Taproot).
        network (str): Rede Bitcoin ('mainnet' ou 'testnet').
    
    Returns:
        dict: Dicionário contendo os saldos em satoshis:
            - "confirmed": Saldo confirmado em satoshis
            - "unconfirmed": Saldo não confirmado em satoshis
            
    Raises:
        requests.exceptions.RequestException: Em caso de erros na comunicação
            com a API. Neste caso, retorna dados simulados para evitar falha completa.
            
    Example:
        >>> get_balance("bc1q34aq5drpuwy3wgl9lhup9892qp6svr8ldzyy7c", "mainnet")
        {
            "confirmed": 1250000,
            "unconfirmed": 50000
        }
    """
    try:
        logger.info(f"[BLOCKCHAIN] Consultando saldo para o endereço {address} na rede {network}")
        
        if network == "testnet":
            url = f"https://blockstream.info/testnet/api/address/{address}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            return {
                "confirmed": data.get("chain_stats", {}).get("funded_txo_sum", 0) - data.get("chain_stats", {}).get("spent_txo_sum", 0),
                "unconfirmed": data.get("mempool_stats", {}).get("funded_txo_sum", 0) - data.get("mempool_stats", {}).get("spent_txo_sum", 0)
            }
        else:
            url = f"{get_blockchain_api_url(network)}/address/{address}/balance"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"[BLOCKCHAIN] Erro ao consultar saldo: {str(e)}")
        
        dummy_data = {"confirmed": 0, "unconfirmed": 0}
        logger.warning(f"[BLOCKCHAIN] Retornando dados simulados: {dummy_data}")
        return dummy_data

def get_utxos(address: str, network: str) -> list:
    """
    Recupera UTXOs (Unspent Transaction Outputs) disponíveis para um endereço Bitcoin.
    
    ## O que são UTXOs?
    
    UTXOs (Unspent Transaction Outputs) são saídas de transações não gastas que 
    pertencem a um endereço. No modelo UTXO do Bitcoin:
    
    * Cada UTXO representa uma quantidade específica de bitcoin
    * Para gastar bitcoins, você precisa referenciar UTXOs existentes como entradas
    * UTXOs são consumidos integralmente em transações
    * Se quiser gastar apenas parte de um UTXO, o restante deve ser enviado de 
      volta para você como troco
    
    Esta função consulta APIs blockchain externas para obter a lista de UTXOs
    disponíveis para um endereço, facilitando a criação de novas transações.
    
    Args:
        address (str): Endereço Bitcoin a ser consultado. Suporta todos os
            formatos de endereço (Legacy, SegWit, Native SegWit, Taproot).
        network (str): Rede Bitcoin ('mainnet' ou 'testnet').
    
    Returns:
        list: Lista de UTXOs disponíveis, onde cada UTXO é representado como
            um dicionário contendo:
            - "txid": ID da transação que contém o UTXO
            - "vout": Índice da saída na transação
            - "value": Valor em satoshis
            - "status": Informações sobre confirmação
            
    Raises:
        requests.exceptions.RequestException: Em caso de erros na comunicação
            com a API. Neste caso, retorna uma lista vazia para evitar falha completa.
            
    Example:
        >>> get_utxos("bc1q34aq5drpuwy3wgl9lhup9892qp6svr8ldzyy7c", "mainnet")
        [
            {
                "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                "vout": 0,
                "value": 50000,
                "status": {
                    "confirmed": true,
                    "block_height": 800000
                }
            }
        ]
    """
    try:
        logger.info(f"[BLOCKCHAIN] Consultando UTXOs para o endereço {address} na rede {network}")
        
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
            url = f"{get_blockchain_api_url(network)}/address/{address}/utxo"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"[BLOCKCHAIN] Erro ao consultar UTXOs: {str(e)}")
        
        dummy_data = []
        logger.warning(f"[BLOCKCHAIN] Retornando dados simulados: {dummy_data}")
        return dummy_data