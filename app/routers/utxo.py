from fastapi import APIRouter
from app.models.utxo_models import TransactionRequest, TransactionResponse
from app.services.utxo_service import build_transaction
from app.dependencies import get_network

router = APIRouter()

@router.post("/", 
            response_model=TransactionResponse,
            summary="Constrói uma transação Bitcoin",
            description="""
Constrói uma transação Bitcoin (não assinada) a partir de UTXOs e saídas especificadas.

## O que é uma transação Bitcoin?

Uma transação Bitcoin contém:
* **Entradas (inputs)**: UTXOs que serão gastos
* **Saídas (outputs)**: Endereços que receberão fundos e valores
* **Taxas**: Diferença entre soma das entradas e soma das saídas

## Como construir uma transação:

1. Selecione UTXOs suficientes para cobrir o valor que deseja enviar
2. Defina os endereços de destino e valores
3. Especifique uma taxa apropriada para confirmação no prazo desejado
4. Construa a transação usando esta API
5. Assine a transação com sua chave privada
6. Transmita a transação para a rede

## Parâmetros do corpo da requisição:

* **inputs**: Lista de UTXOs a serem gastos
  * **txid**: ID da transação que contém o UTXO
  * **vout**: Índice da saída na transação original
  * **value**: Valor do UTXO em satoshis
  * **script**: Script de desbloqueio (opcional)
  * **sequence**: Sequência (opcional)

* **outputs**: Lista de saídas (para onde enviar os fundos)
  * **address**: Endereço Bitcoin de destino
  * **value**: Valor a enviar em satoshis

* **fee_rate**: Taxa em satoshis por byte virtual (sat/vB)

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
  "raw_transaction": "02000000013e283d571fe99cb1ebb...",
  "txid": "a1b2c3d4e5f6...",
  "fee": 10000
}
```

## Observações importantes:

1. A transação retornada NÃO está assinada - use o endpoint `/api/sign` para assiná-la
2. A taxa é calculada como: `(soma_entradas - soma_saídas)`
3. Se não houver change address (endereço de troco), todo o valor excedente será considerado como taxa
4. Transações muito grandes ou com taxas muito baixas podem nunca ser confirmadas
5. Em produção, sempre verifique o TXID e a taxa antes de assinar
            """,
            response_description="Transação não assinada com detalhes")
def create_transaction(request: TransactionRequest) -> TransactionResponse:
    """
    Constrói uma transação Bitcoin a partir de UTXOs e saídas especificadas.
    
    - **inputs**: Lista de UTXOs a serem gastos
    - **outputs**: Lista de saídas (endereços e valores)
    - **fee_rate**: Taxa em satoshis por byte virtual
    
    Retorna a transação raw não assinada, o txid e a taxa calculada.
    """
    network = get_network()
    return build_transaction(request, network)