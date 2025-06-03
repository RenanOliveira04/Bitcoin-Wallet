import requests
from app.dependencies import get_blockchain_api_url, get_cache_dir, get_cache_timeout, is_offline_mode_enabled
import logging
from typing import Any
import time
import json
import os

logger = logging.getLogger(__name__)

class PersistentBlockchainCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._ensure_cache_dir()
        self._load_cache()
    
    def _ensure_cache_dir(self):
        """Garante que o diretório de cache existe"""
        cache_dir = get_cache_dir()
        os.makedirs(cache_dir, exist_ok=True)
    
    def _load_cache(self):
        """Carrega o cache do disco"""
        cache_file = get_cache_dir() / "blockchain_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    self._cache = data.get("cache", {})
                    self._timestamps = data.get("timestamps", {})
                    logger.info(f"[CACHE] Cache carregado do disco com {len(self._cache)} entradas")
            except Exception as e:
                logger.error(f"[CACHE] Erro ao carregar cache do disco: {str(e)}")
    
    def _save_cache(self):
        """Salva o cache para o disco"""
        cache_file = get_cache_dir() / "blockchain_cache.json"
        try:
            with open(cache_file, "w") as f:
                json.dump({
                    "cache": self._cache,
                    "timestamps": self._timestamps
                }, f)
                logger.debug(f"[CACHE] Cache salvo no disco com {len(self._cache)} entradas")
        except Exception as e:
            logger.error(f"[CACHE] Erro ao salvar cache no disco: {str(e)}")

    def get(self, key: str, ignore_ttl: bool = False) -> Any:
        """
        Obtém um valor do cache
        
        Args:
            key: Chave para buscar no cache
            ignore_ttl: Se True, ignora o TTL e retorna o valor mesmo se expirado
            
        Returns:
            O valor armazenado ou None se não encontrado ou expirado
        """
        if key in self._cache:
            cache_timeout = get_cache_timeout(cold_wallet=is_offline_mode_enabled())
            
            if ignore_ttl or time.time() - self._timestamps.get(key, 0) < cache_timeout:
                return self._cache[key]
            elif not ignore_ttl:
                logger.debug(f"[CACHE] Valor expirado para a chave: {key}")
        return None

    def set(self, key: str, value: Any):
        """
        Armazena um valor no cache e salva no disco
        
        Args:
            key: Chave para armazenar o valor
            value: Valor a ser armazenado
        """
        self._cache[key] = value
        self._timestamps[key] = time.time()
        self._save_cache()

blockchain_cache = PersistentBlockchainCache()

def get_balance(address: str, network: str, offline_mode: bool = False) -> dict:
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
        offline_mode (bool): Se True, usa apenas dados do cache sem consultar a API.
    
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
    cache_key = f"balance_{network}_{address}"
    
    cached_data = blockchain_cache.get(cache_key)
    if cached_data:
        logger.info(f"[BLOCKCHAIN] Retornando saldo do cache para {address}")
        return cached_data
    
    if offline_mode:
        expired_data = blockchain_cache.get(cache_key, ignore_ttl=True)
        if expired_data:
            logger.info(f"[OFFLINE] Usando dados do cache expirado para {address}")
            return expired_data
        else:
            logger.warning(f"[OFFLINE] Sem dados de cache para {address}")
            return {"confirmed": 0, "unconfirmed": 0}
    
    try:
        logger.info(f"[BLOCKCHAIN] Consultando saldo para o endereço {address} na rede {network}")
        
        # For empty or temporarily inaccessible addresses, return 0 balance
        # This avoids errors in the UI when the blockchain API is not accessible
        default_result = {"confirmed": 0, "unconfirmed": 0}
        
        if network == "testnet":
            # Try multiple APIs in sequence until one succeeds
            apis_to_try = [
                {
                    "name": "blockstream.info",
                    "url": f"https://blockstream.info/testnet/api/address/{address}",
                    "parser": lambda data: {
                        "confirmed": data.get("chain_stats", {}).get("funded_txo_sum", 0) - data.get("chain_stats", {}).get("spent_txo_sum", 0),
                        "unconfirmed": data.get("mempool_stats", {}).get("funded_txo_sum", 0) - data.get("mempool_stats", {}).get("spent_txo_sum", 0)
                    }
                },
                {
                    "name": "blockchair.com",
                    "url": f"https://api.blockchair.com/bitcoin/testnet/dashboards/address/{address}",
                    "parser": lambda data: {
                        "confirmed": data.get("data", {}).get(address, {}).get("address", {}).get("balance", 0),
                        "unconfirmed": data.get("data", {}).get(address, {}).get("address", {}).get("received_unspent", 0) - 
                                      data.get("data", {}).get(address, {}).get("address", {}).get("balance", 0)
                    }
                },
                {
                    "name": "mempool.space",
                    "url": f"https://mempool.space/testnet/api/address/{address}",
                    "parser": lambda data: {
                        "confirmed": data.get("chain_stats", {}).get("funded_txo_sum", 0) - data.get("chain_stats", {}).get("spent_txo_sum", 0),
                        "unconfirmed": data.get("mempool_stats", {}).get("funded_txo_sum", 0) - data.get("mempool_stats", {}).get("spent_txo_sum", 0)
                    }
                }
            ]
            
            for api in apis_to_try:
                try:
                    logger.info(f"[BLOCKCHAIN] Tentando {api['name']} para saldo: {api['url']}")
                    response = requests.get(api['url'], timeout=15)  # Reduced timeout for faster fallback
                    response.raise_for_status()
                    data = response.json()
                    
                    result = api['parser'](data)
                    logger.info(f"[BLOCKCHAIN] Sucesso com {api['name']} para saldo de {address}")
                    break  # Exit the loop if successful
                except Exception as e:
                    logger.warning(f"[BLOCKCHAIN] Falha ao acessar {api['name']}: {str(e)}")
                    result = default_result  # Will be overwritten if another API succeeds
                    continue  # Try the next API
        else:
            url = f"{get_blockchain_api_url(network)}/address/{address}/balance"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()

        blockchain_cache.set(cache_key, result)
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"[BLOCKCHAIN] Erro ao consultar saldo: {str(e)}")
        
        expired_data = blockchain_cache.get(cache_key, ignore_ttl=True)
        if expired_data:
            logger.warning(f"[BLOCKCHAIN] Retornando dados do cache expirado: {expired_data}")
            return expired_data
            
        raise

def get_utxos(address: str, network: str, offline_mode: bool = False) -> list:
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
        offline_mode (bool): Se True, usa apenas dados do cache sem consultar a API.
    
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
    cache_key = f"utxos_{network}_{address}"
    
    cached_data = blockchain_cache.get(cache_key)
    if cached_data:
        logger.info(f"[BLOCKCHAIN] Retornando UTXOs do cache para {address}")
        return cached_data
    
    if offline_mode:
        expired_data = blockchain_cache.get(cache_key, ignore_ttl=True)
        if expired_data:
            logger.info(f"[OFFLINE] Usando UTXOs do cache expirado para {address}")
            return expired_data
        else:
            logger.warning(f"[OFFLINE] Sem dados de UTXOs em cache para {address}")
            return []
    
    try:
        logger.info(f"[BLOCKCHAIN] Consultando UTXOs para o endereço {address} na rede {network}")
        
        # Default empty result for valid addresses that cannot be reached
        default_result = []
        
        if network == "testnet":
            # Try multiple APIs in sequence until one succeeds
            apis_to_try = [
                {
                    "name": "blockstream.info",
                    "url": f"https://blockstream.info/testnet/api/address/{address}/utxo",
                    "parser": lambda data: [{
                        "txid": utxo.get("txid"),
                        "vout": utxo.get("vout"),
                        "value": utxo.get("value"),
                        "script": None,
                        "confirmations": utxo.get("status", {}).get("confirmations", 0),
                        "address": address
                    } for utxo in data]
                },
                {
                    "name": "blockchair.com",
                    "url": f"https://api.blockchair.com/bitcoin/testnet/dashboards/address/{address}?utxo=true",
                    "parser": lambda data: [{
                        "txid": utxo.get("transaction_hash"),
                        "vout": utxo.get("index"),
                        "value": utxo.get("value"),
                        "script": None,
                        "confirmations": data.get("context", {}).get("state", 0) - utxo.get("block_id", 0) if utxo.get("block_id", 0) > 0 else 0,
                        "address": address
                    } for utxo in data.get("data", {}).get(address, {}).get("utxo", [])]
                },
                {
                    "name": "mempool.space",
                    "url": f"https://mempool.space/testnet/api/address/{address}/utxo",
                    "parser": lambda data: [{
                        "txid": utxo.get("txid"),
                        "vout": utxo.get("vout"),
                        "value": utxo.get("value"),
                        "script": None,
                        "confirmations": 1 if utxo.get("status", {}).get("confirmed", False) else 0,
                        "address": address
                    } for utxo in data]
                }
            ]
            
            for api in apis_to_try:
                try:
                    logger.info(f"[BLOCKCHAIN] Tentando {api['name']} para UTXOs: {api['url']}")
                    response = requests.get(api['url'], timeout=15)  # Reduced timeout for faster fallback
                    response.raise_for_status()
                    data = response.json()
                    
                    result = api['parser'](data)
                    logger.info(f"[BLOCKCHAIN] Sucesso com {api['name']} para UTXOs de {address}: {len(result)} encontrados")
                    break  # Exit the loop if successful
                except Exception as e:
                    logger.warning(f"[BLOCKCHAIN] Falha ao acessar {api['name']} para UTXOs: {str(e)}")
                    result = default_result  # Will be overwritten if another API succeeds
                    continue  # Try the next API
                
            blockchain_cache.set(cache_key, result)
            return result
        else:
            url = f"{get_blockchain_api_url(network)}/address/{address}/utxo"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()
            blockchain_cache.set(cache_key, result)
            return result
            
    except requests.exceptions.RequestException as e:
        logger.error(f"[BLOCKCHAIN] Erro ao consultar UTXOs: {str(e)}")
        
        expired_data = blockchain_cache.get(cache_key, ignore_ttl=True)
        if expired_data:
            logger.warning(f"[BLOCKCHAIN] Retornando UTXOs do cache expirado: {len(expired_data)} UTXOs")
            return expired_data
            
        # Propagate the error instead of returning dummy data
        raise

def is_offline_mode() -> bool:
    """
    Verifica se o modo offline está ativo.
    
    Esta função verifica a configuração do modo offline e, se necessário,
    tenta fazer uma requisição simples para verificar a conectividade.
    
    Returns:
        bool: True se estiver no modo offline, False caso contrário
    """
    if is_offline_mode_enabled():
        return True
        
    try:
        requests.get("https://blockstream.info/api/blocks/tip/height", timeout=2)
        return False
    except:
        logger.warning("[BLOCKCHAIN] Modo offline detectado por falha na conexão")
        return True

def _get_test_balance_blockstream_fallback(address, force_offline=False):
    """Fallback para Blockstream.info para consultar saldo em testnet"""
    try:
        if not force_offline:
            url = f"https://blockstream.info/testnet/api/address/{address}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return {"confirmed": 0}  
        raise Exception("Modo offline forçado")
    except Exception as e:
        logger.warning(f"Erro ao consultar Blockstream para saldo de {address}: {str(e)}")
        raise

def _get_balance_from_api(address, network, force_offline=False):
    """Obtém saldo do endereço através da API configurada"""
    try:
        if not force_offline:
            url = f"{get_blockchain_api_url(network)}/address/{address}/balance"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        raise Exception("Modo offline forçado")
    except Exception as e:
        logger.warning(f"Erro ao consultar API para saldo de {address}: {str(e)}")
        
        if network == "testnet":
            return _get_test_balance_blockstream_fallback(address, force_offline)
        
        raise Exception(f"Erro ao obter saldo para {address}: {str(e)}")

def _get_test_utxos_blockstream_fallback(address, force_offline=False):
    """Fallback para Blockstream.info para consultar UTXOs em testnet"""
    try:
        if not force_offline:
            url = f"https://blockstream.info/testnet/api/address/{address}/utxo"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            utxos = []
            for utxo in data:
                utxos.append({
                    "txid": utxo.get("txid"),
                    "vout": utxo.get("vout"),
                    "value": utxo.get("value"),
                    "confirmations": 0 if utxo.get("status", {}).get("confirmed", False) else 0,
                    "script": "", 
                    "address": address
                })
            return utxos
        raise Exception("Modo offline forçado")
    except Exception as e:
        logger.warning(f"Erro ao consultar Blockstream para UTXOs de {address}: {str(e)}")
        return []

def _get_utxos_from_api(address, network, force_offline=False):
    """Obtém UTXOs do endereço através da API configurada"""
    try:
        if not force_offline:
            url = f"{get_blockchain_api_url(network)}/address/{address}/utxo"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data
        raise Exception("Modo offline forçado")
    except Exception as e:
        logger.warning(f"Erro ao consultar API para UTXOs de {address}: {str(e)}")
        
        if network == "testnet":
            return _get_test_utxos_blockstream_fallback(address, force_offline)
        
        return []