from fastapi import APIRouter
from app.services.blockchain_service import get_balance, get_utxos
from app.dependencies import get_network
from app.models.balance_models import BalanceModel

router = APIRouter()

@router.get("/{address}", 
            summary="Consulta saldo e UTXOs de um endereço Bitcoin",
            description="""
Retorna o saldo disponível e UTXOs (Unspent Transaction Outputs) para um endereço Bitcoin.

## Informações Retornadas:

1. **Saldo**: Valor total disponível no endereço em satoshis (1 BTC = 100.000.000 satoshis)
2. **UTXOs**: Lista detalhada de todas as saídas de transação não gastas que pertencem ao endereço

## Formatos de Endereço Suportados:

* Legacy (P2PKH): Endereços que começam com 1 (mainnet) ou m/n (testnet)
* SegWit (P2SH): Endereços que começam com 3 (mainnet) ou 2 (testnet)
* Native SegWit (P2WPKH): Endereços que começam com bc1q (mainnet) ou tb1q (testnet)
* Taproot (P2TR): Endereços que começam com bc1p (mainnet) ou tb1p (testnet)

## Exemplo de resposta:
```json
{
  "balance": 5000000,
  "utxos": [
    {
      "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
      "vout": 0,
      "value": 3000000,
      "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
      "confirmations": 3,
      "address": "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
    },
    {
      "txid": "9f2c45a12db0144909b5db269415f7319179105982ac70ed80d76ea79d923ebf",
      "vout": 1,
      "value": 2000000,
      "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
      "confirmations": 6,
      "address": "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
    }
  ]
}
```

## Notas:
* O saldo é retornado em satoshis (1 BTC = 100.000.000 satoshis)
* UTXOs com menos de 1 confirmação podem ser considerados não confiáveis
* Recomenda-se verificar as confirmações antes de construir transações
            """,
            response_description="Saldo e UTXOs disponíveis para o endereço",
            response_model=BalanceModel)
def get_balance_utxos(address: str):
    """
    Consulta saldo e UTXOs disponíveis para um endereço Bitcoin.
    
    - **address**: Endereço Bitcoin a ser consultado
    
    Retorna:
    - **balance**: Saldo total disponível em satoshis
    - **utxos**: Lista de UTXOs (saídas não gastas) disponíveis
    """
    network = get_network()
    balance_data = get_balance(address, network)
    utxos_data = get_utxos(address, network)
    return BalanceModel(balance=balance_data['confirmed'], utxos=utxos_data)