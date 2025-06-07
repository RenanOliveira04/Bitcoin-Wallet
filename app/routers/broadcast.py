from fastapi import APIRouter, HTTPException, Depends
from app.models.broadcast_models import BroadcastRequest, BroadcastResponse
import requests
from app.dependencies import get_blockchain_api_url, get_network
import logging
import hashlib
import time
from functools import lru_cache
from typing import Dict, Any, List, Optional
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

router = APIRouter()

def read_varint(data: bytes, index: int) -> Tuple[Optional[int], int]:
    """
    Lê um VarInt (variável inteiro) do formato Bitcoin.
    
    Args:
        data: Dados binários contendo o VarInt
        index: Índice inicial do VarInt nos dados
        
    Returns:
        Tupla (valor, tamanho_em_bytes) ou (None, 0) em caso de erro
    """
    if index >= len(data):
        return None, 0
        
    first_byte = data[index]
    
    if first_byte < 0xfd:
        return first_byte, 1
    elif first_byte == 0xfd:
        if index + 2 > len(data):
            return None, 0
        return int.from_bytes(data[index+1:index+3], 'little'), 3
    elif first_byte == 0xfe:
        if index + 4 > len(data):
            return None, 0
        return int.from_bytes(data[index+1:index+5], 'little'), 5
    else:  # 0xff
        if index + 8 > len(data):
            return None, 0
        return int.from_bytes(data[index+1:index+9], 'little'), 9


def calculate_vsize(tx_bytes: bytes) -> int:
    """
    Calcula o tamanho virtual (vsize) de uma transação em vbytes.
    
    Args:
        tx_bytes: Transação em formato binário
        
    Returns:
        Tamanho virtual em vbytes
    """
    return len(tx_bytes)


def calculate_weight(tx_bytes: bytes) -> int:
    """
    Calcula o 'peso' da transação (weight) conforme definido pelo BIP 141.
    
    Args:
        tx_bytes: Transação em formato binário
        
    Returns:
        Peso da transação (tamanho sem testemunha * 3 + tamanho total)
    """
    return len(tx_bytes) * 4


def calculate_txid(tx_hex: str) -> Optional[str]:
    """
    Calcula o TXID (hash duplo SHA-256) de uma transação.
    
    Args:
        tx_hex: Transação em formato hexadecimal
        
    Returns:
        TXID em hexadecimal ou None em caso de erro
    """
    if not tx_hex:
        return None
    try:
        binary_data = bytes.fromhex(tx_hex)
        hash1 = hashlib.sha256(binary_data).digest()
        txid = hashlib.sha256(hash1).digest()[::-1].hex()
        return txid if len(txid) == 64 else None
    except Exception as e:
        logger.error(f"[BROADCAST] Erro ao calcular TXID: {str(e)}")
        return None


def decode_tx_basic(tx_hex: str) -> dict:
    """
    Faz uma decodificação básica de uma transação Bitcoin para validar sua estrutura.
    
    Esta função verifica:
    - Formato hexadecimal válido
    - Tamanho mínimo da transação
    - Presença de campos obrigatórios
    - Estrutura básica da transação
    
    Args:
        tx_hex: Transação em formato hexadecimal
        
    Returns:
        Dicionário com os resultados da validação
    """
    try:
        if not tx_hex:
            return {"valid": False, "error": "Transação vazia"}
            
        tx_hex = tx_hex.strip()
        if not all(c in '0123456789abcdefABCDEF' for c in tx_hex):
            return {"valid": False, "error": "Formato hexadecimal inválido"}
            
        if len(tx_hex) < 20:  
            return {"valid": False, "error": f"Transação muito curta: {len(tx_hex)//2} bytes"}
        
        try:
            tx_bytes = bytes.fromhex(tx_hex)
            logger.debug(f"[DECODE] Transação convertida para {len(tx_bytes)} bytes")
            logger.debug(f"[DECODE] Primeiros 16 bytes: {tx_bytes[:16].hex()}")
        except (ValueError, TypeError) as e:
            return {"valid": False, "error": f"Erro ao converter hex para bytes: {str(e)}"}
        
        if len(tx_bytes) < 10:  
            return {"valid": False, "error": f"Transação muito curta: {len(tx_bytes)} bytes"}
        
        txid = calculate_txid(tx_hex)
        if not txid or len(txid) != 64 or not all(c in '0123456789abcdef' for c in txid):
            return {"valid": False, "error": "Falha ao calcular TXID"}
            
        if len(tx_bytes) < 4:
            return {"valid": False, "error": "Transação muito curta para conter versão"}
            
        version = int.from_bytes(tx_bytes[0:4], byteorder='little')
        logger.debug(f"[DECODE] Versão da transação: 0x{version:08x}")
            
        index = 4
        
        # Check for SegWit marker and flag
        is_segwit = False
        if index + 2 <= len(tx_bytes) and tx_bytes[index] == 0x00 and tx_bytes[index+1] in [0x01, 0x02]:
            logger.debug("[DECODE] Transação SegWit detectada")
            is_segwit = True
            index += 2  # Skip marker and flag bytes
            
        if index >= len(tx_bytes):
            return {"valid": False, "error": "Fim inesperado dos dados ao ler contador de inputs"}
            
        try:
            input_count, size = read_varint(tx_bytes, index)
            logger.debug(f"[DECODE] Número de inputs: {input_count} (tamanho varint: {size} bytes)")
            
            if input_count is None or input_count < 0:
                return {
                    "valid": False, 
                    "error": f"Número inválido de inputs: {input_count}",
                    "details": {
                        "position": index,
                        "bytes": tx_bytes[index:index+8].hex(),
                        "is_segwit": is_segwit,
                        "context": {
                            "prev_bytes": tx_bytes[max(0, index-8):index].hex(),
                            "next_bytes": tx_bytes[index:index+16].hex()
                        }
                    }
                }
            index += size
            
        except Exception as e:
            logger.error(f"[DECODE] Erro ao ler número de inputs: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "error": f"Erro ao ler número de inputs: {str(e)}",
                "details": {
                    "position": index,
                    "bytes_available": len(tx_bytes) - index,
                    "context_bytes": tx_bytes[max(0, index-8):index+16].hex()
                }
            }
        
        if input_count == 0:
            header_info = {
                "version": version,
                "marker": tx_bytes[4:5].hex() if len(tx_bytes) > 4 else None,
                "flag": tx_bytes[5:6].hex() if len(tx_bytes) > 5 else None,
                "input_count_position": 4,
                "input_count_bytes": tx_bytes[4:4+size].hex() if len(tx_bytes) > 4+size else None
            }
            
            return {
                "valid": False, 
                "error": "Transação sem inputs (não é uma transação padrão)",
                "details": {
                    "txid": txid,
                    "version": f"0x{version:08x}",
                    "tx_size_bytes": len(tx_bytes),
                    "tx_size_hex_chars": len(tx_hex),
                    "header_info": header_info,
                    "first_100_bytes": tx_hex[:200],
                    "suggested_fix": "Verifique se a transação foi serializada corretamente. Certifique-se de que os inputs estão sendo incluídos na transação final."
                }
            }
        
        for i in range(input_count):
            if index + 36 > len(tx_bytes):
                return {"valid": False, "error": f"Fim inesperado dos dados ao ler input {i+1}/{input_count}"}
            
            index += 36
            
            if index >= len(tx_bytes):
                return {"valid": False, "error": f"Fim inesperado dos dados ao ler tamanho do script do input {i+1}"}
                
            script_size, size = read_varint(tx_bytes, index)
            if script_size is None or script_size < 0:
                return {"valid": False, "error": f"Tamanho inválido de script de assinatura no input {i+1}: {script_size}"}
                
            index += size
            
            if index + script_size + 4 > len(tx_bytes):
                return {"valid": False, "error": f"Fim inesperado dos dados ao ler script do input {i+1}"}
                
            index += script_size
            
            if index + 4 > len(tx_bytes):
                return {"valid": False, "error": f"Fim inesperado dos dados ao ler sequência do input {i+1}"}
                
            index += 4
        
        if index >= len(tx_bytes):
            return {"valid": False, "error": "Fim inesperado dos dados ao ler contador de outputs"}
            
        output_count, size = read_varint(tx_bytes, index)
        if output_count is None or output_count < 1:
            return {"valid": False, "error": f"Número inválido de outputs: {output_count}"}
        index += size
        
        for i in range(output_count):
            if index + 8 > len(tx_bytes):
                return {"valid": False, "error": f"Fim inesperado dos dados ao ler valor do output {i+1}"}
                
            index += 8
            
            if index >= len(tx_bytes):
                return {"valid": False, "error": f"Fim inesperado dos dados ao ler tamanho do script do output {i+1}"}
                
            script_size, size = read_varint(tx_bytes, index)
            if script_size is None or script_size < 0:
                return {"valid": False, "error": f"Tamanho inválido de script de bloqueio no output {i+1}: {script_size}"}
                
            index += size
            
            if index + script_size > len(tx_bytes):
                return {"valid": False, "error": f"Fim inesperado dos dados ao ler script do output {i+1}"}
                
            index += script_size
        
        if index + 4 > len(tx_bytes):
            return {"valid": False, "error": "Fim inesperado dos dados ao ler locktime"}
            
        locktime = int.from_bytes(tx_bytes[index:index+4], byteorder='little')
        
        if index + 4 < len(tx_bytes):
            extra_bytes = len(tx_bytes) - (index + 4)
            logger.warning(f"[BROADCAST] Dados adicionais após o fim da transação: {extra_bytes} bytes")
        
        return {
            "valid": True,
            "version": version,
            "txid": txid,
            "input_count": input_count,
            "output_count": output_count,
            "locktime": locktime,
            "size": len(tx_bytes),
            "vsize": calculate_vsize(tx_bytes),
            "weight": calculate_weight(tx_bytes)
        }
        
    except Exception as e:
        logger.error(f"[BROADCAST] Erro ao decodificar transação: {str(e)}", exc_info=True)
        return {"valid": False, "error": f"Erro ao decodificar transação: {str(e)}"}

@lru_cache(maxsize=128)
def get_broadcast_services(network: str, tx_hex: str) -> List[Dict[str, Any]]:
    """
    Retorna a lista de serviços de broadcast configurados para a rede especificada.
    
    Args:
        network: Rede Bitcoin ('mainnet' ou 'testnet')
        tx_hex: Transação em formato hexadecimal (usado para cache)
        
    Returns:
        Lista de dicionários com configurações dos serviços de broadcast
    """
    is_testnet = network == "testnet"
    network_path = "testnet/" if is_testnet else ""
    
    services = [
        {
            "name": "mempool.space",
            "url": f"https://mempool.space/{network_path}api/tx",
            "method": "post",
            "data": tx_hex,  # Send raw hex as request body
            "headers": {"Content-Type": "text/plain"},  # Set proper content type
            "txid_field": "txid",
            "explorer": f"https://mempool.space/{network_path}tx/{{txid}}",
            "priority": 1,
            "timeout": 30,
            "retries": 2
        },
        {
            "name": "blockstream.info",
            "url": f"https://blockstream.info/{network_path}api/tx",
            "method": "post",
            "data": {"tx": tx_hex},
            "txid_field": "txid",
            "explorer": f"https://blockstream.info/{network_path}tx/{{txid}}",
            "priority": 2,
            "timeout": 30,
            "retries": 1
        },
        {
            "name": "blockstream.space",
            "url": f"https://blockstream.space/{network_path}api/tx",
            "method": "post",
            "data": {"tx": tx_hex},
            "txid_field": "txid",
            "explorer": f"https://blockstream.space/{network_path}tx/{{txid}}",
            "priority": 3,
            "timeout": 25,
            "retries": 1
        }
    ]
    
    if not is_testnet:
        services.extend([
            {
                "name": "btc.com",
                "url": "https://chain.api.btc.com/v3/tools/tx-publish",
                "method": "post",
                "data": {"rawhex": tx_hex},
                "txid_field": "data",
                "explorer": f"https://btc.com/{{txid}}",
                "priority": 4,
                "timeout": 20,
                "retries": 1
            },
            {
                "name": "blockcypher.com",
                "url": f"https://api.blockcypher.com/v1/btc/{'test3' if is_testnet else 'main'}/txs/push",
                "method": "post",
                "data": {"tx": tx_hex},
                "txid_field": "tx.hash",
                "explorer": f"https://live.blockcypher.com/btc/{'testnet/' if is_testnet else ''}tx/{{txid}}/",
                "priority": 5,
                "timeout": 20,
                "retries": 1
            }
        ])
    
    services.sort(key=lambda x: x["priority"])
    
    logger.debug(f"[BROADCAST] Configurados {len(services)} serviços de broadcast para {network}")
    return services

async def try_broadcast_to_service(session: aiohttp.ClientSession, service: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tenta transmitir uma transação para um serviço específico.
    
    Args:
        session: Sessão HTTP assíncrona
        service: Dicionário com configurações do serviço
        
    Returns:
        Dicionário com resultado da operação
    """
    start_time = time.time()
    service_name = service["name"]
    
    # Handle both raw tx_hex and JSON data formats
    if isinstance(service["data"], dict):
        tx_hex = service["data"].get("tx") or service["data"].get("data") or service["data"].get("rawhex")
        use_json = True
    else:
        tx_hex = service["data"]
        use_json = False
    
    try:
        logger.info(f"[BROADCAST] Tentando broadcast via {service_name}")
        
        if not tx_hex or len(tx_hex) > 200000:  
            error_msg = "Transação inválida ou muito grande para transmissão"
            logger.error(f"[BROADCAST] {error_msg} via {service_name}")
            return {
                "success": False,
                "error": error_msg,
                "service": service_name,
                "status_code": 413
            }
        
        timeout_seconds = min(30 + (len(tx_hex) // 1000), 120)
        
        # Prepare request parameters
        request_params = {
            'url': service["url"],
            'timeout': aiohttp.ClientTimeout(total=timeout_seconds)
        }
        
        # Add headers and data based on content type
        if use_json:
            request_params['json'] = service["data"]
            request_params['headers'] = {"Content-Type": "application/json"}
        else:
            request_params['data'] = tx_hex
            request_params['headers'] = service.get("headers", {})
        
        # Make the request
        async with session.post(**request_params) as response:
            elapsed = time.time() - start_time
            response_text = (await response.text()).strip()
            
            if response.status == 200:
                txid = None
                try:
                    if response_text.startswith('{"'):
                        response_json = await response.json()
                        txid = response_json.get(service["txid_field"], "") if service.get("txid_field") else None
                        if not txid and isinstance(response_json, dict):
                            txid = next((v for k, v in response_json.items() if k.lower().endswith('txid') or k.lower() == 'result'), None)
                    
                    if not txid:
                        txid = response_text.strip('\"')  
                        if len(txid) != 64 or not all(c in '0123456789abcdefABCDEF' for c in txid):
                            txid = None
                except Exception as json_err:
                    logger.warning(f"[BROADCAST] Erro ao processar resposta JSON de {service_name}: {str(json_err)}")
                
                if not txid:
                    txid = calculate_txid(tx_hex)
                    if txid:
                        logger.debug(f"[BROADCAST] TXID calculado localmente para {service_name}: {txid}")
                
                if not txid:
                    error_msg = "Não foi possível obter ou calcular o TXID da transação"
                    logger.error(f"[BROADCAST] {error_msg} via {service_name}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "service": service_name,
                        "status_code": 400
                    }
                
                logger.info(f"[BROADCAST] Broadcast bem-sucedido via {service_name} em {elapsed:.3f}s")
                
                return {
                    "success": True,
                    "txid": txid,
                    "service": service_name,
                    "explorer_url": service["explorer"].format(txid=txid) if "explorer" in service else None,
                    "response_time": elapsed,
                    "status_code": response.status
                }
            else:
                error_msg = f"Erro {response.status}: {response_text[:200]}"  
                
                status_messages = {
                    400: "Requisição inválida. Verifique o formato da transação.",
                    403: "Acesso negado ao serviço de broadcast.",
                    413: "Transação muito grande para processamento.",
                    429: "Muitas requisições. Tente novamente mais tarde.",
                    500: "Erro interno no servidor de broadcast.",
                    503: "Serviço de broadcast temporariamente indisponível."
                }
                
                if response.status in status_messages:
                    error_msg = f"{status_messages[response.status]} ({response.status})"
                
                logger.warning(f"[BROADCAST] Erro ao transmitir via {service_name} em {elapsed:.3f}s: {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "service": service_name,
                    "status_code": response.status,
                    "response_time": elapsed
                }
                
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        error_msg = f"Timeout ao conectar com {service_name} após {elapsed:.1f}s"
        logger.error(f"[BROADCAST] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "service": service_name,
            "status_code": 504,
            "response_time": elapsed
        }
        
    except aiohttp.ClientError as ce:
        elapsed = time.time() - start_time
        error_msg = f"Erro de conexão com {service_name}: {str(ce)}"
        logger.error(f"[BROADCAST] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "service": service_name,
            "status_code": 503,
            "response_time": elapsed
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Erro inesperado ao tentar {service_name}: {str(e)}"
        logger.error(f"[BROADCAST] {error_msg}", exc_info=True)
        return {
            "success": False,
            "error": error_msg,
            "service": service_name,
            "status_code": 500,
            "response_time": elapsed
        }

@router.post(
    "/",
    summary="Transmite uma transação para a rede Bitcoin",
    description="""
    Transmite (broadcast) uma transação Bitcoin assinada para a rede. Este é o passo final
    após a construção e assinatura da transação.

    ## O que é broadcast de transação?

    Broadcast é o processo de enviar uma transação assinada para a rede Bitcoin, onde:
    1. A transação é primeiro verificada localmente
    2. Em seguida, é propagada para os nós conectados
    3. Os mineradores a incluem em seus mempools
    4. Eventualmente é incluída em um bloco

    ## Processo completo de transação:

    1. Gerar chave e endereço: `POST /api/keys`
    2. Consultar saldo e UTXOs: `GET /api/balance/{address}`
    3. Construir transação: `POST /api/utxo`
    4. Assinar transação: `POST /api/sign`
    5. **Transmitir transação: `POST /api/broadcast`** (este endpoint)
    6. Verificar status: `GET /api/tx/{txid}`
    
    ## Possíveis códigos de erro:
    * **400**: Transação inválida ou rejeitada
    * **409**: Transação conflita com outra (double-spend)
    * **413**: Transação muito grande
    * **429**: Taxa muito baixa ou outras restrições de taxa
    * **503**: Serviço temporariamente indisponível

    ## Observações importantes:
    1. **Transações são irreversíveis** - verifique cuidadosamente antes de transmitir
    2. Transações com taxa muito baixa podem ficar presas no mempool ou serem descartadas
    3. O broadcast não garante confirmação, apenas a propagação inicial
    4. Use o endpoint `/api/tx/{txid}` para monitorar o status da transação após o broadcast
    """,
    response_model=BroadcastResponse
)
async def broadcast_transaction(request: BroadcastRequest):
    """
    Transmite uma transação Bitcoin assinada para a rede Bitcoin.
    
    A transação deve estar completamente assinada e em formato hexadecimal.
    O serviço tentará transmitir para múltiplos nós para garantir a melhor propagação.
    """
    tx_hex = request.tx_hex.strip() if request.tx_hex else ""
    
    logger.debug(f"[BROADCAST] Raw request data: {request}")
    logger.debug(f"[BROADCAST] Raw tx_hex (first 200 chars): {tx_hex[:200]}")
    logger.debug(f"[BROADCAST] Raw tx_hex (last 100 chars): {tx_hex[-100:]}")
    logger.debug(f"[BROADCAST] Transaction length: {len(tx_hex)} characters")
    
    if not tx_hex:
        logger.error("[BROADCAST] Transação vazia")
        raise HTTPException(status_code=400, detail="Transação vazia")
        
    if len(tx_hex) < 10:  
        logger.error(f"[BROADCAST] Transação muito curta: {len(tx_hex)} caracteres")
        raise HTTPException(status_code=400, detail="Transação muito curta para ser válida")
    
    try:
        try:
            tx_bytes = bytes.fromhex(tx_hex)
            logger.debug(f"[BROADCAST] Transação convertida para {len(tx_bytes)} bytes")
            
            logger.debug(f"[BROADCAST] Primeiros 32 bytes: {tx_bytes[:32].hex()}")
            
            if len(tx_bytes) >= 4:
                version = int.from_bytes(tx_bytes[0:4], byteorder='little')
                logger.debug(f"[BROADCAST] Versão da transação: 0x{version:08x}")
            
        except ValueError as e:
            logger.error(f"[BROADCAST] Formato hexadecimal inválido: {str(e)}")
            raise HTTPException(status_code=400, detail="Formato hexadecimal inválido")
        
        if tx_bytes[0] not in [0x01, 0x02]:  
            logger.warning(f"[BROADCAST] Versão de transação incomum: 0x{tx_bytes[0]:02x}")
            
        logger.debug(f"[BROADCAST] Iniciando decodificação da transação. Tamanho: {len(tx_bytes)} bytes")
            
        tx_decode = decode_tx_basic(tx_hex)
        if not tx_decode["valid"]:
            error_msg = tx_decode["error"]
            logger.warning(f"[BROADCAST] Transação inválida detectada: {error_msg}")
            logger.debug(f"[BROADCAST] Detalhes da validação: {tx_decode.get('details', 'Nenhum detalhe adicional')}")
            
            logger.debug(f"[BROADCAST] Dados brutos da transação (hex): {tx_hex}")
            
            raise HTTPException(
                status_code=400, 
                detail=f"Transação inválida: {error_msg}",
                headers={"X-Error-Details": str(tx_decode.get('details', ''))}
            )
        
        txid = tx_decode.get("txid", "")
        logger.info(f"[BROADCAST] Transação válida, TXID: {txid}, versão: {tx_decode.get('version', 'desconhecida')}")
        logger.info(f"[BROADCAST] Tamanho: {len(tx_hex)//2} bytes")
        
        calculated_txid = calculate_txid(tx_hex)
        if calculated_txid and txid and calculated_txid != txid:
            logger.warning(f"[BROADCAST] TXID calculado localmente difere: {calculated_txid} vs {txid}")
        
        network = get_network()
        services = get_broadcast_services(network, tx_hex)
        logger.info(f"[BROADCAST] Iniciando broadcast para {len(services)} serviços")
        
        async with aiohttp.ClientSession() as session:
            successful_result = None
            errors = []
            broadcast_start = time.time()
            
            for service in services:
                try:
                    logger.info(f"[BROADCAST] Tentando serviço: {service['name']}")
                    result = await try_broadcast_to_service(session, service)
                    
                    if isinstance(result, dict) and result.get("success"):
                        successful_result = result
                        txid = successful_result.get("txid", txid)
                        logger.info(f"[BROADCAST] Sucesso no serviço {service['name']}")
                        break  
                        
                except Exception as e:
                    error_msg = f"{service['name']}: {str(e)}"
                    logger.error(f"[BROADCAST] Erro no serviço {service['name']}: {str(e)}")
                    errors.append(error_msg)
            
            broadcast_time = time.time() - broadcast_start
            
            if successful_result:
                response_data = {
                    "txid": txid,
                    "status": "sent",
                    "explorer_url": f"https://blockstream.info/{'testnet/' if network == 'testnet' else ''}tx/{txid}",
                    "broadcast_service": successful_result.get('service', 'unknown'),
                    "time_elapsed": broadcast_time
                }
                
                logger.info(f"[BROADCAST] Transação {txid} transmitida com sucesso")
                return response_data
            else:
                error_msg = "Falha ao transmitir para todos os serviços"
                if errors:
                    error_msg += f": {', '.join(errors[:3])}"
                    if len(errors) > 3:
                        error_msg += f"... (+{len(errors)-3} mais)"
                
                logger.error(f"[BROADCAST] {error_msg}")
                
                status_code = 400
                if any("already in block chain" in e.lower() for e in errors):
                    status_code = 409
                elif any("insufficient fee" in e.lower() for e in errors):
                    status_code = 429
                
                raise HTTPException(status_code=status_code, detail=error_msg)
    
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"[BROADCAST] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar transação: {str(e)}")