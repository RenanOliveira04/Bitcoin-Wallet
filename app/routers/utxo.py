# app/routers/utxo.py
from fastapi import APIRouter, HTTPException
from app.models.utxo_models import TransactionRequest, TransactionResponse
from app.services.utxo_service import build_transaction
from app.dependencies import get_network
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Transações"],
    responses={
        400: {"description": "Requisição inválida"},
        500: {"description": "Erro ao construir transação"}
    }
)

@router.post("/", 
            summary="Constrói uma transação Bitcoin",
            description="""
Constrói uma transação Bitcoin a partir de UTXOs (entradas) e destinatários (saídas).

## Como funcionam as transações Bitcoin:

No Bitcoin, transações consomem UTXOs (Unspent Transaction Outputs) e criam novos UTXOs:

1. **Entradas**: UTXOs existentes que serão gastos (referenciados por txid e vout)
2. **Saídas**: Novos UTXOs que serão criados (endereço e valor)
3. **Taxa**: Diferença entre a soma das entradas e a soma das saídas

## Detalhes das Entradas (UTXOs):

Cada entrada (UTXO) deve conter:
* **txid**: ID da transação que contém o UTXO
* **vout**: Índice da saída na transação original
* **value**: Valor em satoshis
* **script** (opcional): Script de bloqueio
* **address** (opcional): Endereço associado ao UTXO

## Detalhes das Saídas:

Cada saída deve conter:
* **address**: Endereço do destinatário
* **value**: Valor a ser enviado em satoshis

## Cálculo da Taxa:

A taxa é calculada como: `soma_das_entradas - soma_das_saídas`

Para determinar uma taxa adequada:
* Use o endpoint `/api/fee/estimate` para obter taxas recomendadas
* Multiplique a taxa (em sat/vB) pelo tamanho estimado da transação

## Parâmetros:

* **inputs**: Lista de UTXOs a serem gastos
* **outputs**: Lista de destinatários e valores
* **fee_rate** (opcional): Taxa em sat/vB para o cálculo automático

## Exemplo de requisição:
```json
{
  "inputs": [
    {
      "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
      "vout": 0,
      "value": 50000,
      "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
      "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2"
    }
  ],
  "outputs": [
    {
      "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
      "value": 49000
    }
  ],
  "fee_rate": 10.0
}
```

## Exemplo de resposta:
```json
{
  "raw_transaction": "02000000013e283d571fe99cb1ebb0c012ec8fcfb785d4a39e45d48636e67ea85dce01a7a000000000000000000010c1700000000000016001414c1403f4591940d6ee7488b66d0ac650f61e60f00000000",
  "txid": "27effe2c5c8dc7b87a9ba4e8a4c48fff12d0c50e625d810424d1e1c3b05d5feb",
  "inputs_count": 1,
  "outputs_count": 1,
  "total_input": 50000,
  "total_output": 49000,
  "fee": 1000,
  "estimated_size": 100,
  "estimated_fee_rate": 10.0
}
```

## Próximos passos:

1. Assinar a transação com `/api/sign`
2. Validar a transação com `/api/validate`
3. Transmitir a transação com `/api/broadcast`
            """,
            response_model=TransactionResponse)
def build_transaction(request: TransactionRequest):
    """
    Constrói uma transação Bitcoin a partir de UTXOs e destinatários.
    
    - **inputs**: Lista de UTXOs a serem gastos
    - **outputs**: Lista de destinatários e valores
    - **fee_rate**: Taxa em sat/vB para o cálculo automático
    
    Retorna a transação construída e informações sobre ela.
    """
    try:
        return build_transaction(
            request=request,
            network=get_network()
        )
    except Exception as e:
        logger.error(f"Erro ao construir transação: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))