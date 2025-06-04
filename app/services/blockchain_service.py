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
        cache_dir = get_cache_dir()
        os.makedirs(cache_dir, exist_ok=True)
    
    def _load_cache(self):
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
        if key in self._cache:
            cache_timeout = get_cache_timeout(cold_wallet=is_offline_mode_enabled())
            
            if ignore_ttl or time.time() - self._timestamps.get(key, 0) < cache_timeout:
                return self._cache[key]
            elif not ignore_ttl:
                logger.debug(f"[CACHE] Valor expirado para a chave: {key}")
        return None

    def set(self, key: str, value: Any):
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
        
        default_result = {"confirmed": 0, "unconfirmed": 0}
        
        if network == "testnet":
            apis_to_try = [
                {
                    "name": "mempool.space",
                    "url": f"https://mempool.space/testnet/api/address/{address}",
                    "parser": lambda data: {
                        "confirmed": data.get("chain_stats", {}).get("funded_txo_sum", 0) - data.get("chain_stats", {}).get("spent_txo_sum", 0),
                        "unconfirmed": data.get("mempool_stats", {}).get("funded_txo_sum", 0) - data.get("mempool_stats", {}).get("spent_txo_sum", 0)
                    },
                    "timeout": 10,
                    "priority": 1
                },
                {
                    "name": "blockstream.info",
                    "url": f"https://blockstream.info/testnet/api/address/{address}",
                    "parser": lambda data: {
                        "confirmed": data.get("chain_stats", {}).get("funded_txo_sum", 0) - data.get("chain_stats", {}).get("spent_txo_sum", 0),
                        "unconfirmed": data.get("mempool_stats", {}).get("funded_txo_sum", 0) - data.get("mempool_stats", {}).get("spent_txo_sum", 0)
                    },
                    "timeout": 15,
                    "priority": 2
                },
                {
                    "name": "blockcypher.com",
                    "url": f"https://api.blockcypher.com/v1/btc/test3/addrs/{address}/balance",
                    "parser": lambda data: {
                        "confirmed": data.get("final_balance", 0),
                        "unconfirmed": data.get("unconfirmed_balance", 0) - data.get("final_balance", 0)
                    },
                    "timeout": 15,
                    "priority": 3
                },
                {
                    "name": "blockchair.com",
                    "url": f"https://api.blockchair.com/bitcoin/testnet/dashboards/address/{address}",
                    "parser": lambda data: {
                        "confirmed": data.get("data", {}).get(address, {}).get("address", {}).get("balance", 0),
                        "unconfirmed": data.get("data", {}).get(address, {}).get("address", {}).get("received_unspent", 0) - 
                                      data.get("data", {}).get(address, {}).get("address", {}).get("balance", 0)
                    },
                    "timeout": 20,
                    "priority": 4
                }
            ]
            
            apis_to_try.sort(key=lambda x: x.get("priority", 999))
            result = default_result
            last_error = None
            
            for api in apis_to_try:
                try:
                    logger.info(f"[BLOCKCHAIN] Tentando {api['name']} para saldo: {api['url']}")
                    response = requests.get(api['url'], timeout=api.get('timeout', 10))
                    response.raise_for_status()
                    data = response.json()
                    
                    result = api['parser'](data)
                    logger.info(f"[BLOCKCHAIN] Sucesso com {api['name']} para saldo de {address}")
                    break
                            
                except Exception as e:
                    last_error = e
                    logger.warning(f"[BLOCKCHAIN] Falha ao acessar {api['name']}: {str(e)}")
                    if api == apis_to_try[-1]:
                        raise last_error
                    continue
        else:
            apis_to_try = [
                {
                    "name": "mempool.space",
                    "url": f"https://mempool.space/api/address/{address}",
                    "parser": lambda data: {
                        "confirmed": data.get("chain_stats", {}).get("funded_txo_sum", 0) - data.get("chain_stats", {}).get("spent_txo_sum", 0),
                        "unconfirmed": data.get("mempool_stats", {}).get("funded_txo_sum", 0) - data.get("mempool_stats", {}).get("spent_txo_sum", 0)
                    },
                    "timeout": 10,
                    "priority": 1
                },
                {
                    "name": "blockstream.info",
                    "url": f"https://blockstream.info/api/address/{address}",
                    "parser": lambda data: {
                        "confirmed": data.get("chain_stats", {}).get("funded_txo_sum", 0) - data.get("chain_stats", {}).get("spent_txo_sum", 0),
                        "unconfirmed": data.get("mempool_stats", {}).get("funded_txo_sum", 0) - data.get("mempool_stats", {}).get("spent_txo_sum", 0)
                    },
                    "timeout": 15,
                    "priority": 2
                }
            ]
            
            apis_to_try.sort(key=lambda x: x.get("priority", 999))
            result = default_result
            last_error = None
            
            for api in apis_to_try:
                try:
                    logger.info(f"[BLOCKCHAIN] Tentando {api['name']} para saldo: {api['url']}")
                    response = requests.get(api['url'], timeout=api.get('timeout', 10))
                    response.raise_for_status()
                    data = response.json()
                    
                    result = api['parser'](data)
                    logger.info(f"[BLOCKCHAIN] Sucesso com {api['name']} para saldo de {address}")
                    break
                            
                except Exception as e:
                    last_error = e
                    logger.warning(f"[BLOCKCHAIN] Falha ao acessar {api['name']}: {str(e)}")
                    if api == apis_to_try[-1]:
                        raise last_error
                    continue
            
        blockchain_cache.set(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"[BLOCKCHAIN] Erro ao obter saldo para {address}: {str(e)}")
        return default_result

def get_utxos(address: str, network: str, offline_mode: bool = False, force_cache: bool = False) -> list:
    cache_key = f"utxos_{network}_{address}"
    
    if not force_cache:
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
            logger.warning(f"[OFFLINE] Sem dados de cache para UTXOs de {address}")
            return []
    
    try:
        start_time = time.time()
        logger.info(f"[BLOCKCHAIN] UTXO: Consultando para {address} ({network})")
        
        if network == "testnet":
            apis_to_try = [
                {
                    "name": "mempool.space",
                    "url": f"https://mempool.space/testnet/api/address/{address}/utxo",
                    "parser": lambda data, addr=address: [{
                        "txid": utxo.get("txid"),
                        "vout": utxo.get("vout"),
                        "value": utxo.get("value"),
                        "script": utxo.get("scriptpubkey", ""),
                        "confirmations": utxo.get("status", {}).get("confirmed", False) and utxo.get("status", {}).get("block_height", 0) or 0,
                        "address": addr
                    } for utxo in data],
                    "timeout": 10,
                    "priority": 1
                },
                {
                    "name": "blockstream.info",
                    "url": f"https://blockstream.info/testnet/api/address/{address}/utxo",
                    "parser": lambda data, addr=address: [{
                        "txid": utxo.get("txid"),
                        "vout": utxo.get("vout"),
                        "value": utxo.get("value"),
                        "script": utxo.get("scriptpubkey", ""),
                        "confirmations": utxo.get("confirmations", 0),
                        "address": addr
                    } for utxo in data],
                    "timeout": 15,
                    "priority": 2
                },
                {
                    "name": "blockcypher.com",
                    "url": f"https://api.blockcypher.com/v1/btc/test3/addrs/{address}?unspentOnly=true&includeScript=true",
                    "parser": lambda data, addr=address: [{
                        "txid": utxo.get("tx_hash"),
                        "vout": utxo.get("tx_output_n"),
                        "value": utxo.get("value"),
                        "script": utxo.get("script"),
                        "confirmations": utxo.get("confirmations", 0),
                        "address": addr
                    } for utxo in data.get("txrefs", []) if utxo.get("spent_by") is None],
                    "timeout": 15,
                    "priority": 3
                },
                {
                    "name": "blockchair.com",
                    "url": f"https://api.blockchair.com/bitcoin/testnet/dashboards/address/{address}?utxo=true",
                    "parser": lambda data, addr=address: [{
                        "txid": utxo.get("transaction_hash"),
                        "vout": utxo.get("index"),
                        "value": utxo.get("value"),
                        "script": utxo.get("script_hex", ""),
                        "confirmations": data.get("context", {}).get("state", 0) - utxo.get("block_id", 0) if utxo.get("block_id", 0) > 0 else 0,
                        "address": addr
                    } for utxo in data.get("data", {}).get(address, {}).get("utxo", [])],
                    "timeout": 20,
                    "priority": 4
                }
            ]
        else:
            apis_to_try = [
                {
                    "name": "mempool.space",
                    "url": f"https://mempool.space/api/address/{address}/utxo",
                    "parser": lambda data, addr=address: [{
                        "txid": utxo.get("txid"),
                        "vout": utxo.get("vout"),
                        "value": utxo.get("value"),
                        "script": utxo.get("scriptpubkey", ""),
                        "confirmations": utxo.get("status", {}).get("confirmed", False) and utxo.get("status", {}).get("block_height", 0) or 0,
                        "address": addr
                    } for utxo in data],
                    "timeout": 10,
                    "priority": 1
                },
                {
                    "name": "blockstream.info",
                    "url": f"https://blockstream.info/api/address/{address}/utxo",
                    "parser": lambda data, addr=address: [{
                        "txid": utxo.get("txid"),
                        "vout": utxo.get("vout"),
                        "value": utxo.get("value"),
                        "script": utxo.get("scriptpubkey", ""),
                        "confirmations": utxo.get("confirmations", 0),
                        "address": addr
                    } for utxo in data],
                    "timeout": 15,
                    "priority": 2
                }
            ]
        
        apis_to_try.sort(key=lambda x: x.get("priority", 999))
        last_error = None
        result = []
        
        for api in apis_to_try:
            try:
                logger.info(f"[BLOCKCHAIN] UTXO: Tentando {api['name']} para {address}")
                response = requests.get(api['url'], timeout=api.get('timeout', 10))
                response.raise_for_status()
                data = response.json()
                
                result = api['parser'](data)
                logger.info(f"[BLOCKCHAIN] UTXO: Sucesso com {api['name']} para {address} ({len(result)} UTXOs)")
                break
                        
            except Exception as e:
                last_error = e
                logger.warning(f"[BLOCKCHAIN] UTXO: Falha ao acessar {api['name']}: {str(e)}")
                if api == apis_to_try[-1]:
                    logger.error(f"[BLOCKCHAIN] UTXO: Todas as APIs falharam para {address}")
                    if last_error:
                        raise last_error
                continue
        
        if not result and last_error:
            raise last_error
        
        for utxo in result:
            if 'script' not in utxo or utxo['script'] is None:
                utxo['script'] = ''
            
            if 'value' in utxo and not isinstance(utxo['value'], int):
                try:
                    utxo['value'] = int(utxo['value'])
                except (ValueError, TypeError):
                    utxo['value'] = 0
            
            if 'vout' in utxo and not isinstance(utxo['vout'], int):
                try:
                    utxo['vout'] = int(utxo['vout'])
                except (ValueError, TypeError):
                    utxo['vout'] = 0
            
            if 'confirmations' in utxo and not isinstance(utxo['confirmations'], int):
                try:
                    utxo['confirmations'] = int(utxo['confirmations'])
                except (ValueError, TypeError):
                    utxo['confirmations'] = 0
        
        result = sorted(result, key=lambda utxo: utxo.get('value', 0), reverse=True)
        
        blockchain_cache.set(cache_key, result)
        
        elapsed = time.time() - start_time
        logger.info(f"[BLOCKCHAIN] UTXO: Consulta para {address} completada em {elapsed:.3f}s, {len(result)} UTXOs encontrados")
        
        return result
            
    except requests.exceptions.RequestException as e:
        logger.error(f"[BLOCKCHAIN] UTXO: Erro ao consultar: {str(e)}")
        
        expired_data = blockchain_cache.get(cache_key, ignore_ttl=True)
        if expired_data:
            logger.warning(f"[BLOCKCHAIN] UTXO: Retornando {len(expired_data)} UTXOs do cache expirado após erro")
            return expired_data
            
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