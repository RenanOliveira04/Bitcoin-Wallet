# app/routers/tx.py
from fastapi import APIRouter, HTTPException, Path, Query, Body, Request
from app.models.transaction_status_models import TransactionStatusModel
from app.models.utxo_models import TransactionRequest, TransactionResponse
from app.services.tx_status_service import get_transaction_status
from app.services.transaction.tx_builder_service import build_transaction
from app.dependencies import get_network
import logging
import time
from typing import Optional

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

* **Status**: Estado atual da transação (confirmed, confirming, pending, unknown)
* **Confirmações**: Número de blocos confirmando a transação
* **Bloco**: Altura e hash do bloco onde a transação foi incluída
* **Timestamp**: Data e hora da confirmação
* **Link para Explorador**: URL para visualizar a transação em um explorador de blockchain

## Status da Transação:

* **confirmed**: Transação tem 6+ confirmações, considerada irreversível
* **confirming**: Transação tem 1-5 confirmações, em processo de confirmação
* **pending**: Transação está no mempool, aguardando inclusão em um bloco
* **unknown**: Transação não encontrada ou API indisponível
* **unknown_cached**: Dados de uma transação anteriormente desconhecida, obtidos do cache
* **confirmed_cached**: Dados confirmados obtidos do cache (pode estar desatualizado)

## Parâmetros:

* **txid**: ID da transação (hash de 64 caracteres hexadecimais)
* **network**: Rede Bitcoin (mainnet ou testnet)
* **force_refresh**: (opcional) Force uma nova consulta ignorando o cache

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
* O endpoint usa cache inteligente com TTL baseado no número de confirmações
* Use force_refresh=true para obter dados atualizados ignorando o cache
            """,
            response_model=TransactionStatusModel)
def get_tx_status(
    txid: str = Path(..., min_length=64, max_length=64, description="ID da transação (hash de 64 caracteres hexadecimais)"),
    network: str = Query(None, description="Rede Bitcoin (mainnet ou testnet)"),
    force_refresh: bool = Query(False, description="Ignorar cache e forçar nova consulta à API")
):
    """
    Consulta o status atual de uma transação Bitcoin.
    
    - **txid**: ID da transação (hash de 64 caracteres hexadecimais)
    - **network**: Rede Bitcoin (mainnet ou testnet)
    - **force_refresh**: Se True, ignora o cache e força uma nova consulta
    
    Retorna informações detalhadas sobre o status da transação.
    """
    try:
        start_time = time.time()
        logger.info(f"[TX_ENDPOINT] Requisição de status para txid={txid}, network={network}, force_refresh={force_refresh}")
        
        network = network or get_network()
        result = get_transaction_status(txid, network, force_refresh)
        
        elapsed = time.time() - start_time
        logger.info(f"[TX_ENDPOINT] Resposta gerada em {elapsed:.3f}s: status={result.status}, confirmations={result.confirmations}")
        
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[TX_ENDPOINT] Erro ao consultar status da transação após {elapsed:.3f}s: {str(e)}", exc_info=True)
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

* O campo `fee_rate` é em satoshis por byte
* O troco é calculado automaticamente e enviado de volta ao primeiro endereço de input
* Certifique-se de que o total de saídas + taxa seja igual ao total de entradas
            """,
            response_model=TransactionResponse)
async def build_tx(
    request: Request,
    network: str = Query(None, description="Rede Bitcoin (mainnet ou testnet)"),
    builder_type: Optional[str] = Query("bitcoinlib", description="Tipo de builder a ser utilizado (bitcoinlib ou bitcoincore)")
):
    """
    Constrói uma transação Bitcoin não assinada.
    
    - **network**: Rede Bitcoin (mainnet ou testnet)
    - **builder_type**: Tipo de builder a ser utilizado (bitcoinlib ou bitcoincore)
    
    Retorna a transação raw não assinada em formato hexadecimal.
    """
    try:
        start_time = time.time()
        raw_request = await request.json()
        logger.info(f"[TX_BUILD] Recebendo requisição bruta: {raw_request}")
        
        if 'inputs' in raw_request and not raw_request['inputs']:
            logger.error(f"[TX_BUILD] Lista de inputs vazia fornecida diretamente na requisição")
            raise HTTPException(status_code=400, detail="Lista de inputs vazia")
    except Exception as e:
        logger.error(f"[TX_BUILD] Erro ao ler corpo da requisição: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao ler corpo da requisição: {str(e)}")
    
    try:
        if 'from_address' in raw_request and 'inputs' not in raw_request:
            logger.info(f"[TX_BUILD] Detectado formato do frontend, convertendo para formato do backend")
            from app.services.blockchain_service import get_utxos
            
            from_address = raw_request['from_address']
            net = network or get_network()
            
            utxos = get_utxos(from_address, net, force_cache=True)
            
            if not utxos:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Não há UTXOs disponíveis para o endereço {from_address}"
                )
            
            inputs = []
            inputs_append = inputs.append
            
            for utxo in utxos:
                inputs_append({
                    'txid': utxo['txid'],
                    'vout': utxo['vout'],
                    'value': utxo['value'],
                    'script': utxo.get('script', ''),
                    'address': from_address
                })
            
            raw_request['inputs'] = inputs
            del raw_request['from_address']
            
            adapter_time = time.time() - start_time
            logger.info(f"[TX_BUILD] Convertido para formato do backend: {len(inputs)} inputs em {adapter_time:.3f}s")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TX_BUILD] Erro ao converter formato: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Erro ao processar UTXOs: {str(e)}")
    
    if 'inputs' in raw_request and not raw_request['inputs']:
        raise HTTPException(status_code=400, detail=f"Não há UTXOs disponíveis para realizar a transação")
    
    try:
        tx_request = TransactionRequest(**raw_request)
    except Exception as validation_error:
        logger.error(f"[TX_BUILD] Erro de validação Pydantic: {str(validation_error)}")
        error_detail = str(validation_error)
        raise HTTPException(status_code=422, detail=f"Erro de validação: {error_detail}")
    
    try:
        network = network or get_network()
        logger.info(f"[TX_BUILD] Recebida solicitação para construir transação na rede {network} usando builder {builder_type}")
        
        logger.info(f"[TX_BUILD] Detalhes da requisição:")
        logger.info(f"[TX_BUILD] Inputs: {len(tx_request.inputs)}")
        
        for i, input_tx in enumerate(tx_request.inputs):
            logger.info(f"[TX_BUILD] Input {i}: txid={input_tx.txid}, vout={input_tx.vout}, value={input_tx.value}, script={repr(input_tx.script)}, address={input_tx.address}")
        
        logger.info(f"[TX_BUILD] Outputs: {len(tx_request.outputs)}")
        for i, output in enumerate(tx_request.outputs):
            logger.info(f"[TX_BUILD] Output {i}: address={output.address}, value={output.value}")
        
        valid_builders = ["bitcoinlib", "bitcoincore"]
        if builder_type.lower() not in valid_builders:
            logger.warning(f"[TX_BUILD] Tipo de builder inválido: {builder_type}. Utilizando bitcoinlib como padrão.")
            builder_type = "bitcoinlib"
        
        for input_tx in tx_request.inputs:
            if input_tx.script is None:
                input_tx.script = ""
                logger.info(f"[TX_BUILD] Script None convertido para string vazia para input txid={input_tx.txid}, vout={input_tx.vout}")
        
        result = build_transaction(tx_request, network, builder_type)
        total_time = time.time() - start_time
        logger.info(f"[TX_BUILD] Transação construída com sucesso: {result.txid} em {total_time:.3f}s")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TX_BUILD] Erro ao construir transação: {str(e)}", exc_info=True)
        error_detail = str(e)
        status_code = 500
        
        if hasattr(e, 'detail') and isinstance(e.detail, str):
            error_detail = e.detail
            
        
        raise HTTPException(status_code=status_code, detail=error_detail)