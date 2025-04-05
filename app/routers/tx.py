from fastapi import APIRouter, HTTPException, Query
from app.services.tx_status_service import get_transaction_status
from app.dependencies import get_network
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{txid}", 
          summary="Consulta o status de uma transação na blockchain",
          description="""
Verifica o status atual de uma transação Bitcoin na blockchain, retornando informações
como número de confirmações, bloco que a inclui, e timestamp.

## Estados possíveis de uma transação:

1. **mempool**: Transação foi transmitida mas ainda não foi incluída em um bloco
2. **confirmed**: Transação está em um bloco (tem pelo menos 1 confirmação)
3. **not_found**: Transação não foi encontrada (pode não ter sido transmitida ou foi rejeitada)

## O que são confirmações?

Cada novo bloco minerado após o bloco que contém sua transação adiciona uma "confirmação".
O padrão da indústria considera:
* **1 confirmação**: Transação está em um bloco (baixa segurança)
* **3 confirmações**: Segurança moderada
* **6+ confirmações**: Alta segurança, geralmente considerada irreversível

## Informações retornadas:

* **status**: Estado atual da transação
* **confirmations**: Número de confirmações (0 para transações no mempool)
* **block_height**: Altura do bloco onde a transação foi incluída
* **block_hash**: Hash do bloco que contém a transação
* **timestamp**: Data e hora estimada da confirmação
* **explorer_url**: URL para visualizar a transação em um explorador de blockchain

## Parâmetros:

* **txid**: ID da transação (hash de 64 caracteres hexadecimais)
* **network**: Rede Bitcoin (mainnet ou testnet)

## Exemplo de resposta para transação confirmada:
```json
{
  "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
  "status": "confirmed",
  "confirmations": 3,
  "block_height": 2420074,
  "block_hash": "00000000000000a093320ceadfe83feb6c6f2bbad7db282de9e3d7c4cc2ae75a",
  "timestamp": "2023-09-28T15:23:45Z",
  "explorer_url": "https://blockstream.info/testnet/tx/7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e"
}
```

## Exemplo de resposta para transação no mempool:
```json
{
  "txid": "9f2c45a12db0144909b5db269415f7319179105982ac70ed80d76ea79d923ebf",
  "status": "mempool",
  "confirmations": 0,
  "timestamp": "2023-09-28T16:05:12Z",
  "explorer_url": "https://blockstream.info/testnet/tx/9f2c45a12db0144909b5db269415f7319179105982ac70ed80d76ea79d923ebf"
}
```
          """,
          response_description="Status atual e detalhes da transação na blockchain")
def get_tx_status(
    txid: str,
    network: str = Query(None, description="Rede Bitcoin: mainnet ou testnet")
):
    """
    Consulta o status de uma transação Bitcoin.
    
    - **txid**: ID da transação a ser consultada
    - **network**: Rede Bitcoin (testnet ou mainnet)
    
    Retorna o status atual da transação, confirmações e link para explorador.
    """
    try:
        if not network:
            network = get_network()
        
        result = get_transaction_status(txid, network)
        
        return result
    except Exception as e:
        logger.error(f"Erro na rota de status de transação: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e)) 