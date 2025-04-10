# app/routers/tx.py
from fastapi import APIRouter, HTTPException, Path, Query
from app.models.transaction_status_models import TransactionStatusModel
from app.services.tx_status_service import get_transaction_status
from app.dependencies import get_network
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Consultas"],
    responses={
        400: {"description": "Requisição inválida"},
        404: {"description": "Transação não encontrada"},
        500: {"description": "Erro ao consultar status da transação"}
    }
)

@router.get("/{txid}", 
            summary="Consulta o status de uma transação Bitcoin",
            description="""
Consulta o status atual de uma transação Bitcoin na blockchain, incluindo confirmações,
bloco, timestamp e link para explorador.

## Ciclo de Vida de uma Transação Bitcoin:

1. **Transmitida (Mempool)**: A transação foi enviada para a rede, mas ainda não foi incluída em um bloco
2. **Confirmada (1+ confirmações)**: A transação foi incluída em um bloco
3. **Estabelecida (6+ confirmações)**: A transação tem confirmações suficientes para ser considerada irreversível

## Informações Retornadas:

* **Status**: Estado atual da transação (confirmed, pending, not_found)
* **Confirmações**: Número de blocos confirmando a transação
* **Bloco**: Altura e hash do bloco onde a transação foi incluída
* **Timestamp**: Data e hora da confirmação
* **Link para Explorador**: URL para visualizar a transação em um explorador de blockchain

## Verificação de Confirmações:

* **0 confirmações**: Transação no mempool, ainda não incluída em um bloco
* **1-5 confirmações**: Transação confirmada, mas reversível em caso de reorganização da blockchain
* **6+ confirmações**: Transação considerada irreversível (padrão para valores significativos)

## Parâmetros:

* **txid**: ID da transação (hash de 64 caracteres hexadecimais)
* **network**: Rede Bitcoin (mainnet ou testnet)

## Exemplo de resposta:
```json
{
  "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
  "status": "confirmed",
  "confirmations": 6,
  "block_height": 800000,
  "block_hash": "000000000000000000024e33c89641ef59af8bf60fdc2f32ff369b32260930ff",
  "timestamp": "2023-04-01T12:00:00Z",
  "explorer_url": "https://blockstream.info/testnet/tx/7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e"
}
```

## Observações:

* Uma transação precisa de pelo menos 1 confirmação para ser considerada válida
* Para valores significativos, recomenda-se esperar 6+ confirmações
* Transações podem ser rejeitadas da mempool se tiverem taxa muito baixa
            """,
            response_model=TransactionStatusModel)
def get_tx_status(
    txid: str = Path(..., min_length=64, max_length=64, description="ID da transação (hash de 64 caracteres hexadecimais)"),
    network: str = Query(None, description="Rede Bitcoin (mainnet ou testnet)")
):
    """
    Consulta o status atual de uma transação Bitcoin.
    
    - **txid**: ID da transação (hash de 64 caracteres hexadecimais)
    - **network**: Rede Bitcoin (mainnet ou testnet)
    
    Retorna informações detalhadas sobre o status da transação.
    """
    try:
        network = network or get_network()
        result = get_transaction_status(txid, network)
        return result
    except Exception as e:
        logger.error(f"Erro ao consultar status da transação: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Erro ao consultar transação: {str(e)}")