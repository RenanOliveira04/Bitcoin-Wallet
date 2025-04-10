from fastapi import APIRouter, HTTPException, Path
from app.services.blockchain_service import get_balance, get_utxos
from app.dependencies import get_network
from app.models.balance_models import BalanceModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

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
                404: {"description": "Endereço não encontrado ou formato inválido"},
                500: {"description": "Erro ao consultar a blockchain"}
            })
def get_balance_utxos(address: str = Path(..., description="Endereço Bitcoin a ser consultado")):
    """
    Consulta o saldo e UTXOs disponíveis para um endereço Bitcoin.
    
    - **address**: Endereço Bitcoin no formato compatível com a rede
    
    Retorna o saldo total e a lista de UTXOs disponíveis.
    """
    try:
        network = get_network()
        balance_data = get_balance(address, network)
        utxos_data = get_utxos(address, network)
        return BalanceModel(
            balance=balance_data['confirmed'],
            utxos=utxos_data
        )
    except Exception as e:
        logger.error(f"Erro ao consultar saldo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao consultar saldo: {str(e)}")