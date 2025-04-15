# app/routers/tx.py
from fastapi import APIRouter, HTTPException, Path, Query, Body
from app.models.transaction_status_models import TransactionStatusModel
from app.models.utxo_models import TransactionRequest, TransactionResponse
from app.services.tx_status_service import get_transaction_status
from app.services.transaction.tx_builder_service import build_transaction
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

@router.post("/build", 
            summary="Constrói uma transação Bitcoin não assinada",
            description="""
Constrói uma transação Bitcoin não assinada com base nos inputs e outputs fornecidos.

## Como funciona:

1. Você fornece os inputs (UTXOs) que deseja gastar
2. Especifica os outputs (endereços e valores) para onde enviar os bitcoins
3. Opcionalmente, pode especificar a taxa de mineração (em sat/vB)
4. A API retorna a transação raw não assinada e seu TXID

## Inputs Necessários:

* **inputs**: Lista de UTXOs a serem gastos, cada um contendo:
  * txid: ID da transação que criou o UTXO
  * vout: Índice da saída na transação
  * value: Valor em satoshis
  * script: Script de bloqueio (opcional)
  * sequence: Número de sequência (opcional)
  * address: Endereço associado (opcional)

* **outputs**: Lista de destinos, cada um contendo:
  * address: Endereço Bitcoin de destino
  * value: Valor em satoshis a enviar

* **fee_rate**: Taxa de mineração em sat/vB (opcional)

## Exemplo de requisição:
```json
{
  "inputs": [
    {
      "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
      "vout": 0,
      "value": 5000000,
      "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac"
    }
  ],
  "outputs": [
    {
      "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
      "value": 4990000
    }
  ],
  "fee_rate": 2.0
}
```

## Exemplo de resposta:
```json
{
  "raw_transaction": "02000000013e283d571fe99cb1ebb0c012ec2c8bf785f5a39435de8636e67a65ec80daea17000000006a47304402204b3b868a9a17698b37f17c35d58a6383ec5226a8e68b39d90648b9cfd46633bf02204cff73c675f01a2ea7bf6bf80440f3f0e1bbb91e3c95064493b0ccc8a97c1352012103a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8dffffffff0150c30000000000001976a914d0c59903c5bac2868760e90fd521a4665aa7652088ac00000000",
  "txid": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "fee": 10000
}
```

## Observações:

* A transação retornada NÃO está assinada e precisa ser assinada antes de ser transmitida
* Use o endpoint /sign para assinar a transação com sua chave privada
* Os inputs devem corresponder a UTXOs não gastos associados à sua chave
* Certifique-se de que o total de saídas + taxa seja igual ao total de entradas
            """,
            response_model=TransactionResponse)
def build_tx(
    tx_request: TransactionRequest = Body(..., description="Dados da transação a ser construída"),
    network: str = Query(None, description="Rede Bitcoin (mainnet ou testnet)")
):
    """
    Constrói uma transação Bitcoin não assinada.
    
    - **tx_request**: Detalhes da transação, incluindo inputs e outputs
    - **network**: Rede Bitcoin (mainnet ou testnet)
    
    Retorna a transação raw não assinada em formato hexadecimal.
    """
    try:
        network = network or get_network()
        logger.info(f"[TX_BUILD] Recebida solicitação para construir transação na rede {network}")
        
        result = build_transaction(tx_request, network)
        return result
    except Exception as e:
        logger.error(f"[TX_BUILD] Erro ao construir transação: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao construir transação: {str(e)}")