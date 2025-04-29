from fastapi import APIRouter, HTTPException
from app.models.broadcast_models import BroadcastRequest, BroadcastResponse
import requests
from app.dependencies import get_blockchain_api_url
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", 
            summary="Transmite uma transação para a rede Bitcoin",
            description="""
Transmite (broadcast) uma transação Bitcoin assinada para a rede. Este é o passo final
depois de construir e assinar uma transação.

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

## Parâmetros:

* **tx_hex**: Transação Bitcoin assinada em formato hexadecimal

## Exemplo de resposta:
```json
{
  "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
  "status": "sent",
  "explorer_url": "https://blockstream.info/testnet/tx/7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e"
}
```

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
            response_model=BroadcastResponse)
def broadcast_transaction(request: BroadcastRequest):
    """
    Transmite uma transação Bitcoin assinada para a rede.
    
    - **tx_hex**: Transação assinada em formato hexadecimal
    
    Retorna o TXID e link para explorador de blockchain.
    """
    try:
        url = f"{get_blockchain_api_url()}/tx"
        response = requests.post(url, json={"tx": request.tx_hex}, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Erro ao transmitir transação: {response.text}")
            raise HTTPException(
                status_code=400, 
                detail=f"Erro ao transmitir transação: {response.text}"
            )
        
        tx_data = response.json()
        txid = tx_data.get("txid", "unknown")
        
        explorer_url = f"https://blockchair.com/bitcoin/transaction/{txid}"
        
        return {
            "status": "sent",
            "txid": txid,
            "explorer_url": explorer_url
        }
    except Exception as e:
        logger.error(f"Erro no broadcast: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))