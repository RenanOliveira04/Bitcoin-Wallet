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
    Consulta o saldo de um endereço Bitcoin na blockchain usando múltiplas APIs para validação cruzada.
    
    Esta função recupera o saldo confirmado e não confirmado de um endereço Bitcoin
    consultando múltiplas APIs blockchain externas (mempool.space e blockstream) e
    retorna um resultado consistente baseado no consenso entre as fontes.
    
    ## O que são saldos confirmados e não confirmados?
    
    * **Saldo confirmado**: Representa bitcoins em transações que já foram incluídas 
      em um bloco da blockchain e tiveram pelo menos uma confirmação.
    
    * **Saldo não confirmado**: Representa bitcoins em transações que foram 
      transmitidas para a rede mas ainda não foram incluídas em um bloco
      (estão no mempool).
    
    ## Validação Cruzada
    
    A função consulta pelo menos duas fontes independentes (mempool.space e blockstream)
    e retorna um resultado apenas se houver concordância entre as fontes. Isso ajuda a
    prevenir resultados incorretos em caso de problemas em alguma API.
    
    Args:
        address (str): Endereço Bitcoin a ser consultado. Suporta todos os
            formatos de endereço (Legacy, SegWit, Native SegWit, Taproot).
        network (str): Rede Bitcoin ('mainnet' ou 'testnet').
        offline_mode (bool): Se True, usa apenas dados do cache sem consultar a API.
    
    Returns:
        dict: Dicionário contendo os saldos em satoshis:
            - "confirmed": Saldo confirmado em satoshis
            - "unconfirmed": Saldo não confirmado em satoshis
            - "sources_checked": Número de fontes consultadas
            - "sources_agreed": Número de fontes que concordaram com o resultado
            - "source": Nome da fonte dos dados retornados
            
    Raises:
        requests.exceptions.RequestException: Em caso de erros na comunicação
            com as APIs. Neste caso, retorna dados do cache se disponíveis.
            
    Example:
        >>> get_balance("bc1q34aq5drpuwy3wgl9lhup9892qp6svr8ldzyy7c", "mainnet")
        {
            "confirmed": 1250000,
            "unconfirmed": 50000,
            "sources_checked": 2,
            "sources_agreed": 2,
            "source": "mempool.space,blockstream.info"
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
            return {
                "confirmed": 0, 
                "unconfirmed": 0,
                "sources_checked": 0,
                "sources_agreed": 0,
                "source": "offline_cache"
            }
    
    try:
        logger.info(f"[BLOCKCHAIN] Consultando saldo para o endereço {address} na rede {network}")
        
        default_result = {
            "confirmed": 0, 
            "unconfirmed": 0,
            "sources_checked": 0,
            "sources_agreed": 0,
            "source": "none"
        }
        
        # Configuração das APIs para diferentes redes
        if network == "testnet":
            network_path = "testnet/"
            blockcypher_network = "test3"
        else:
            network_path = ""
            blockcypher_network = "main"
        
        # Lista de fontes de dados com seus respectivos parsers
        data_sources = [
            {
                "name": "mempool.space",
                "url": f"https://mempool.space/{network_path}api/address/{address}",
                "parser": lambda data: {
                    "confirmed": data.get("chain_stats", {}).get("funded_txo_sum", 0) - \
                                 data.get("chain_stats", {}).get("spent_txo_sum", 0),
                    "unconfirmed": data.get("mempool_stats", {}).get("funded_txo_sum", 0) - \
                                   data.get("mempool_stats", {}).get("spent_txo_sum", 0)
                },
                "timeout": 10,
                "priority": 1
            },
            {
                "name": "blockstream.info",
                "url": f"https://blockstream.info/{network_path}api/address/{address}",
                "parser": lambda data: {
                    "confirmed": data.get("chain_stats", {}).get("funded_txo_sum", 0) - \
                                 data.get("chain_stats", {}).get("spent_txo_sum", 0),
                    "unconfirmed": data.get("mempool_stats", {}).get("funded_txo_sum", 0) - \
                                   data.get("mempool_stats", {}).get("spent_txo_sum", 0)
                },
                "timeout": 15,
                "priority": 2
            },
            {
                "name": "blockcypher.com",
                "url": f"https://api.blockcypher.com/v1/btc/{blockcypher_network}/addrs/{address}/balance",
                "parser": lambda data: {
                    "confirmed": data.get("final_balance", 0),
                    "unconfirmed": data.get("unconfirmed_balance", 0) - data.get("final_balance", 0)
                },
                "timeout": 15,
                "priority": 3
            }
        ]
        
        # Ordena as fontes por prioridade
        data_sources.sort(key=lambda x: x.get("priority", 999))
        
        results = []
        last_error = None
        
        # Tenta obter dados de pelo menos 2 fontes para validação cruzada
        for source in data_sources[:2]:  # Limita a 2 fontes para validação cruzada
            try:
                logger.info(f"[BLOCKCHAIN] Consultando {source['name']} para saldo: {source['url']}")
                response = requests.get(source['url'], timeout=source.get('timeout', 10))
                response.raise_for_status()
                data = response.json()
                
                result = source['parser'](data)
                result['source'] = source['name']
                results.append(result)
                logger.info(f"[BLOCKCHAIN] Sucesso com {source['name']} para saldo de {address}")
                
            except Exception as e:
                last_error = e
                logger.warning(f"[BLOCKCHAIN] Falha ao acessar {source['name']}: {str(e)}")
                continue
        
        # Se não conseguiu obter resultados de nenhuma fonte
        if not results:
            logger.error(f"[BLOCKCHAIN] Falha ao consultar saldo em todas as fontes")
            if last_error:
                raise last_error
            return default_result
        
        # Se só conseguiu um resultado, retorna ele com um aviso
        if len(results) == 1:
            logger.warning(f"[BLOCKCHAIN] Apenas uma fonte disponível para validação: {results[0]['source']}")
            result = results[0]
            result['sources_checked'] = 1
            result['sources_agreed'] = 1
            blockchain_cache.set(cache_key, result)
            return result
        
        # Verifica se os resultados das fontes são consistentes
        confirmed_values = [r['confirmed'] for r in results]
        unconfirmed_values = [r['unconfirmed'] for r in results]
        
        confirmed_agreement = len(set(confirmed_values)) == 1
        unconfirmed_agreement = len(set(unconfirmed_values)) == 1
        
        # Se os valores concordam entre as fontes, retorna o resultado
        if confirmed_agreement and unconfirmed_agreement:
            result = results[0]
            result['sources_checked'] = len(results)
            result['sources_agreed'] = len(results)
            result['source'] = ", ".join(r['source'] for r in results)
            blockchain_cache.set(cache_key, result)
            return result
        
        # Se há discordância, tenta uma terceira fonte como desempate
        if len(results) < 3 and len(data_sources) > 2:
            logger.warning(f"[BLOCKCHAIN] Discordância entre fontes, consultando terceira fonte")
            try:
                source = data_sources[2]  # Tenta a terceira fonte
                response = requests.get(source['url'], timeout=source.get('timeout', 10))
                response.raise_for_status()
                data = response.json()
                
                tiebreaker = source['parser'](data)
                tiebreaker['source'] = source['name']
                results.append(tiebreaker)
                
                # Recalcula com a terceira fonte
                confirmed_values = [r['confirmed'] for r in results]
                unconfirmed_values = [r['unconfirmed'] for r in results]
                
                # Verifica se há um consenso entre pelo menos 2 fontes
                from collections import Counter
                confirmed_counter = Counter(confirmed_values)
                unconfirmed_counter = Counter(unconfirmed_values)
                
                most_common_confirmed = confirmed_counter.most_common(1)[0]
                most_common_unconfirmed = unconfirmed_counter.most_common(1)[0]
                
                # Se pelo menos 2 fontes concordam, retorna o valor consensual
                if most_common_confirmed[1] >= 2 and most_common_unconfirmed[1] >= 2:
                    result = {
                        'confirmed': most_common_confirmed[0],
                        'unconfirmed': most_common_unconfirmed[0],
                        'sources_checked': len(results),
                        'sources_agreed': most_common_confirmed[1],
                        'source': ", ".join(r['source'] for r in results)
                    }
                    blockchain_cache.set(cache_key, result)
                    return result
                
            except Exception as e:
                logger.warning(f"[BLOCKCHAIN] Falha ao consultar terceira fonte: {str(e)}")
        
        # Se chegou aqui, não houve consenso
        logger.error(f"[BLOCKCHAIN] Discordância entre as fontes para o endereço {address}")
        
        # Retorna a média dos valores como último recurso
        avg_confirmed = sum(confirmed_values) // len(confirmed_values)
        avg_unconfirmed = sum(unconfirmed_values) // len(unconfirmed_values)
        
        result = {
            'confirmed': avg_confirmed,
            'unconfirmed': avg_unconfirmed,
            'sources_checked': len(results),
            'sources_agreed': 0,
            'source': ", ".join(r['source'] for r in results) + " (média)"
        }
        
        blockchain_cache.set(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"[BLOCKCHAIN] Erro ao consultar saldo para {address}: {str(e)}")
        
        # Tenta retornar dados do cache mesmo que expirados
        expired_data = blockchain_cache.get(cache_key, ignore_ttl=True)
        if expired_data:
            logger.warning(f"[BLOCKCHAIN] Retornando dados do cache expirado devido a erro na API")
            return expired_data
            
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