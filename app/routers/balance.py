from fastapi import APIRouter, HTTPException, Path, Query
from app.services.blockchain_service import get_balance, get_utxos, is_offline_mode
from app.dependencies import get_network
from app.models.balance_models import BalanceModel
import logging
from bitcoinlib.keys import Address
from typing import Optional
import re
import requests

logger = logging.getLogger(__name__)

router = APIRouter()

def validate_bitcoin_address(address: str, network: str) -> bool:
    """
    Valida se um endereço Bitcoin é válido para a rede especificada.
    
    Args:
        address (str): Endereço Bitcoin a ser validado
        network (str): Rede Bitcoin ('mainnet' ou 'testnet')
        
    Returns:
        bool: True se o endereço for válido, False caso contrário
    """
    try:
        if network == "testnet":
            if re.match(r'^[mn][a-km-zA-HJ-NP-Z1-9]{25,34}$', address):
                return True
            # SegWit (P2SH)
            if re.match(r'^2[a-km-zA-HJ-NP-Z1-9]{25,34}$', address):
                return True
            # Native SegWit (P2WPKH)
            if re.match(r'^tb1[a-zA-HJ-NP-Z0-9]{39,59}$', address):
                return True
        else:  # mainnet
            if re.match(r'^1[a-km-zA-HJ-NP-Z1-9]{25,34}$', address):
                return True
            # SegWit (P2SH)
            if re.match(r'^3[a-km-zA-HJ-NP-Z1-9]{25,34}$', address):
                return True
            # Native SegWit (P2WPKH)
            if re.match(r'^bc1[a-zA-HJ-NP-Z0-9]{39,59}$', address):
                return True
        
        try:
            addr = Address.import_address(address)
            if network == "testnet":
                return addr.is_testnet
            return not addr.is_testnet
        except Exception as e:
            logger.debug(f"Falha na validação com bitcoinlib: {str(e)}")
            
        if network == "testnet" and address.startswith("tb1"):
            return True
        if network == "mainnet" and address.startswith("bc1"):
            return True
            
        return False
    except Exception as e:
        logger.error(f"Erro na validação de endereço: {str(e)}")
        return False

@router.get("/{address}", 
            summary="Consulta saldo e UTXOs de um endereço",
            description="""
Consulta o saldo disponível e UTXOs (Unspent Transaction Outputs) para um endereço Bitcoin.

## O que são UTXOs?

UTXOs (Unspent Transaction Outputs) são saídas de transações não gastas que pertencem a um 
endereço. No modelo UTXO do Bitcoin:

* Cada UTXO representa uma quantidade específica de bitcoin
* Para gastar bitcoins, você precisa referenciar UTXOs existentes como entradas
* UTXOs são consumidos integralmente em transações
* Se quiser gastar apenas parte de um UTXO, o restante deve ser enviado de volta para você como troco

## Informações retornadas:

1. **Saldo total**: Soma de todos os UTXOs disponíveis
2. **Lista de UTXOs**: Detalhes de cada UTXO disponível, incluindo:
   * txid: ID da transação que criou o UTXO
   * vout: Índice da saída na transação
   * value: Valor em satoshis
   * script: Script de bloqueio
   * confirmações: Número de confirmações
   * endereço: Endereço associado

## Formato do Endereço:

* Compatível com todos os formatos de endereço:
   * Legacy (P2PKH): começa com 1 (mainnet) ou m/n (testnet)
   * SegWit (P2SH): começa com 3 (mainnet) ou 2 (testnet)
   * Native SegWit (P2WPKH): começa com bc1 (mainnet) ou tb1 (testnet)
   * Taproot (P2TR): começa com bc1p (mainnet) ou tb1p (testnet)

## Exemplo de resposta:
```json
{
  "balance": 150000,
  "utxos": [
    {
      "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
      "vout": 0,
      "value": 50000,
      "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
      "confirmations": 6,
      "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2"
    },
    {
      "txid": "8b9ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d284f",
      "vout": 1,
      "value": 100000,
      "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
      "confirmations": 3,
      "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2"
    }
  ]
}
```

## Observações:

* O saldo mostra apenas UTXOs confirmados (pelo menos 1 confirmação)
* Para endereços recém-criados ou sem fundos, a lista de UTXOs estará vazia
* Os valores são expressos em satoshis (1 BTC = 100,000,000 satoshis)
            """,
            response_model=BalanceModel,
            responses={
                400: {"description": "Endereço inválido"},
                404: {"description": "Endereço não encontrado"},
                429: {"description": "Muitas requisições"},
                500: {"description": "Erro ao consultar a blockchain"}
            })
def get_balance_utxos(
    address: str = Path(..., description="Endereço Bitcoin a ser consultado"),
    network: Optional[str] = None,
    force_offline: bool = Query(False, description="Forçar modo offline (usar apenas cache local)")
):
    """
    Consulta o saldo e UTXOs disponíveis para um endereço Bitcoin.
    
    - **address**: Endereço Bitcoin no formato compatível com a rede
    - **network**: Rede Bitcoin ('mainnet' ou 'testnet'). Se não especificado,
                  usa a rede configurada no ambiente.
    - **force_offline**: Se True, usa apenas dados do cache local sem consultar a blockchain
    
    Retorna o saldo total e a lista de UTXOs disponíveis.
    """
    try:
        network = network or get_network()
        
        offline_mode = force_offline or is_offline_mode()
        if offline_mode:
            logger.info(f"[BALANCE] Operando em modo offline para o endereço {address}")
        
        if not validate_bitcoin_address(address, network):
            logger.warning(f"[BALANCE] Endereço inválido ou incompatível: {address} para rede {network}")
            if not offline_mode:
                raise HTTPException(
                    status_code=400,
                    detail=f"Endereço Bitcoin inválido para a rede {network}"
                )
        
        try:
            balance_data = get_balance(address, network, offline_mode)
        except requests.exceptions.Timeout as e:
            logger.warning(f"[BALANCE] Timeout ao consultar saldo para {address}: {str(e)}")
            balance_data = get_balance(address, network, True)
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"[BALANCE] Erro de conexão ao consultar saldo para {address}: {str(e)}")
            balance_data = get_balance(address, network, True)
        
        try:
            utxos_data = get_utxos(address, network, offline_mode)
        except requests.exceptions.Timeout as e:
            logger.warning(f"[BALANCE] Timeout ao consultar UTXOs para {address}: {str(e)}")
            utxos_data = get_utxos(address, network, True)
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"[BALANCE] Erro de conexão ao consultar UTXOs para {address}: {str(e)}")
            utxos_data = get_utxos(address, network, True)
            
        if not offline_mode and balance_data["confirmed"] == 0 and balance_data["unconfirmed"] == 0 and not utxos_data:
            logger.info(f"[BALANCE] Endereço válido mas sem fundos: {address}")
            return BalanceModel(
                balance=0,
                utxos=[]
            )
        
        return BalanceModel(
            balance=balance_data['confirmed'],
            utxos=utxos_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao consultar saldo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar saldo: {str(e)}"
        )